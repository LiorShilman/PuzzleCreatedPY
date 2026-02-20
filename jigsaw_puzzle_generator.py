
import numpy as np
from PIL import Image, ImageDraw
import os

# קבועים גלובליים
t_FEMALE = 1
t_MALE = 2
t_LINE = 3

# פרמטרים ברירת מחדל
DEFAULT_ARC_RATIO = 0.07
DEFAULT_CONNECT_RATIO = 0.3
DEFAULT_POINT_NUM = 300


def computeBezierPoint(points, t):
    """חישוב נקודה על עקומת בזייה מעוקבת"""
    tSquared = t * t
    tCubed = tSquared * t

    cx = 3.0 * (points[1][0] - points[0][0])
    bx = 3.0 * (points[2][0] - points[1][0]) - cx
    ax = points[3][0] - points[0][0] - cx - bx

    cy = 3.0 * (points[1][1] - points[0][1])
    by = 3.0 * (points[2][1] - points[1][1]) - cy
    ay = points[3][1] - points[0][1] - cy - by

    x = (ax * tCubed) + (bx * tSquared) + (cx * t) + points[0][0]
    y = (ay * tCubed) + (by * tSquared) + (cy * t) + points[0][1]

    return (x, y)


def computerBezier(points, num):
    """יצירת מערך נקודות על העקומה"""
    dt = 1.0 / num
    curvePoints = []
    for i in range(num):
        p = computeBezierPoint(points, dt * i)
        curvePoints.append(p)
    return curvePoints


class PieceInfo:
    """מחלקה לניהול מידע על חלקי הפאזל"""
    def __init__(self, size, rowNum, colNum, ar=DEFAULT_ARC_RATIO, cr=DEFAULT_CONNECT_RATIO):
        self.w = size[0] / colNum
        self.h = size[1] / rowNum
        self.rowNum = rowNum
        self.colNum = colNum
        self.arcRatio = ar
        self.connectRatio = cr

    def getPieceInfo(self, row, col):
        arcW = self.w * self.arcRatio
        arcH = self.h * self.arcRatio
        connectW = self.w * self.connectRatio
        connectH = self.h * self.connectRatio

        t = t_MALE if (row + col) % 2 == 0 else t_FEMALE

        if t == t_FEMALE:
            borders = [t_MALE, t_FEMALE, t_MALE, t_FEMALE]
        else:
            borders = [t_FEMALE, t_MALE, t_FEMALE, t_MALE]

        # קצוות
        if col == 0: borders[1] = t_LINE
        if row == 0: borders[2] = t_LINE
        if row + 1 == self.rowNum: borders[0] = t_LINE
        if col + 1 == self.colNum: borders[3] = t_LINE

        # חישוב מיקום
        topX = self.w * col
        topY = self.h * row
        bottomX = self.w * (col + 1)
        bottomY = self.h * (row + 1)
        centerX = self.w * 0.5
        centerY = self.h * 0.5

        # התאמות לפי סוג הקצה
        if borders[0] == t_MALE:
            bottomY += (connectW - arcH)
        elif borders[0] == t_FEMALE:
            bottomY += arcH

        if borders[1] == t_MALE:
            topX -= (connectH - arcW)
            centerX += (connectH - arcW)
        elif borders[1] == t_FEMALE:
            topX -= arcW
            centerX += arcW

        if borders[2] == t_MALE:
            topY -= (connectW - arcH)
            centerY += (connectW - arcH)
        elif borders[2] == t_FEMALE:
            topY -= arcH
            centerY += arcH

        if borders[3] == t_MALE:
            bottomX += (connectH - arcW)
        elif borders[3] == t_FEMALE:
            bottomX += arcW

        return (
            (int(round(topX)), int(round(topY)),
             int(round(bottomX)), int(round(bottomY))),
            (centerX, centerY),
            borders
        )


class PieceOutLine:
    """מחלקה ליצירת קווי מתאר של חלקי הפאזל"""
    def __init__(self, width, height, ar=DEFAULT_ARC_RATIO, cr=DEFAULT_CONNECT_RATIO):
        self.w = width
        self.h = height
        self.arcRatio = ar
        self.connectRatio = cr
        self.pointNum = DEFAULT_POINT_NUM
        # היסט סקלבילי לעקומת Bezier במקום ערך קבוע של 8
        self._curve_offset = min(width, height) * 0.02

    def genRightFemaleArc(self, istop):
        halfW = self.w * 0.5
        halfH = self.h * 0.5
        arcW = self.w * self.arcRatio
        connectW = self.h * self.connectRatio

        top = (halfW, -halfH)
        bottom = (halfW + arcW, -connectW * 0.5)
        dw = bottom[0] - top[0]
        dh = bottom[1] - top[1]
        offset = self._curve_offset

        points = [
            top,
            (top[0] + dw / 3 + offset, top[1] + dh / 3),
            (top[0] + 2 * dw / 3 + offset, top[1] + dh * 2 / 3),
            bottom
        ]

        if not istop:
            return computerBezier(points, self.pointNum)
        else:
            left = [(p[0], -p[1]) for p in reversed(points)]
            return computerBezier(left, self.pointNum)

    def genRightFemaleConnect(self, left):
        halfW = self.w * 0.5
        arcW = self.w * self.arcRatio
        connectW = self.h * self.connectRatio

        startX = halfW + arcW
        startY = -connectW * 0.5
        endX = startX - connectW
        endY = 0

        points = [
            (startX, startY),
            (endX + (startX - endX) * 3 / 5, -startY * 2 / 3),
            (endX, 2 * startY),
            (endX, endY)
        ]

        if not left:
            return computerBezier(points, self.pointNum)
        else:
            left = [(p[0], -p[1]) for p in reversed(points)]
            return computerBezier(left, self.pointNum)

    def genRightFemale(self):
        rightArc = self.genRightFemaleArc(False)
        right = self.genRightFemaleConnect(False)
        left = self.genRightFemaleConnect(True)
        leftArc = self.genRightFemaleArc(True)
        return rightArc + right + left + leftArc

    def genRightMale(self):
        halfW = self.w * 0.5
        points = self.genRightFemale()
        return [(p[0] + (halfW - p[0]) * 2, p[1]) for p in points]

    def genRightLine(self):
        return [(self.w * 0.5, self.h * 0.5)]

    def genLeftMale(self):
        halfW = self.w * 0.5
        points = self.genRightFemale()
        return list(reversed([(p[0] - halfW * 2, p[1]) for p in points]))

    def genLeftFemale(self):
        halfW = self.w * 0.5
        points = self.genLeftMale()
        return [(((-p[0] - halfW) * 2 + p[0]), p[1]) for p in points]

    def genLeftLine(self):
        return [(-self.w * 0.5, -self.h * 0.5)]

    def genBottomFemale(self):
        rightArc = self.genBottomFemaleArc(False)
        right = self.genBottomFemaleConnect(False)
        left = self.genBottomFemaleConnect(True)
        leftArc = self.genBottomFemaleArc(True)
        return rightArc + right + left + leftArc

    def genBottomFemaleArc(self, isLeft):
        halfW = self.w * 0.5
        halfH = self.h * 0.5
        arcH = self.h * self.arcRatio
        connectW = self.w * self.connectRatio

        right = (halfW, halfH)
        left = (connectW * 0.5, halfH + arcH)
        dw = right[0] - left[0]
        dh = left[1] - right[1]
        offset = self._curve_offset

        points = [
            right,
            (right[0] - dw / 3, right[1] + dh / 3 + offset),
            (right[0] - 2 * dw / 3, right[1] + dh * 2 / 3 + offset),
            left
        ]

        if not isLeft:
            return computerBezier(points, self.pointNum)
        else:
            left = [(-p[0], p[1]) for p in reversed(points)]
            return computerBezier(left, self.pointNum)

    def genBottomFemaleConnect(self, left):
        halfH = self.h * 0.5
        arcH = self.h * self.arcRatio
        connectW = self.w * self.connectRatio

        startX = connectW * 0.5
        startY = halfH + arcH
        endX = 0
        endY = startY - connectW

        points = [
            (startX, startY),
            (-startX * 2 / 3, endY + (startY - endY) * 3 / 5),
            (2 * startX, endY),
            (endX, endY)
        ]

        if not left:
            return computerBezier(points, self.pointNum)
        else:
            left = [(-p[0], p[1]) for p in reversed(points)]
            return computerBezier(left, self.pointNum)

    def genBottomMale(self):
        halfH = self.h * 0.5
        points = self.genBottomFemale()
        return [(p[0], (halfH - p[1]) * 2 + p[1]) for p in points]

    def genBottomLine(self):
        return [(-self.w * 0.5, self.h * 0.5)]

    def genTopMale(self):
        points = self.genBottomFemale()
        return list(reversed([(p[0], p[1] - self.h) for p in points]))

    def genTopFemale(self):
        halfH = self.h * 0.5
        points = self.genTopMale()
        return [(p[0], (-p[1] - halfH) * 2 + p[1]) for p in points]

    def genTopLine(self):
        return [(self.w * 0.5, -self.h * 0.5)]

    def genOutLine(self, pieceBorders):
        curvPoints = [(self.w * 0.5, self.h * 0.5)]

        funcs = [
            {t_FEMALE: self.genBottomFemale, t_MALE: self.genBottomMale, t_LINE: self.genBottomLine},
            {t_FEMALE: self.genLeftFemale, t_MALE: self.genLeftMale, t_LINE: self.genLeftLine},
            {t_FEMALE: self.genTopFemale, t_MALE: self.genTopMale, t_LINE: self.genTopLine},
            {t_FEMALE: self.genRightFemale, t_MALE: self.genRightMale, t_LINE: self.genRightLine},
        ]

        for i, f in enumerate(funcs):
            curvPoints.extend(f[pieceBorders[i]]())

        return curvPoints


def polygonCropImage(im, polygon, name):
    """חיתוך תמונה לפי פוליגון"""
    imArray = np.asarray(im)
    maskIm = Image.new('L', (imArray.shape[1], imArray.shape[0]), 0)
    ImageDraw.Draw(maskIm).polygon(polygon, outline=1, fill=1)
    mask = np.array(maskIm)

    newImArray = np.empty(imArray.shape, dtype='uint8')
    newImArray[:, :, :3] = imArray[:, :, :3]
    newImArray[:, :, 3] = mask * 255

    newIm = Image.fromarray(newImArray, "RGBA")
    newIm.save(name)


def createPuzzlePieces(image_input, rows, cols, output_prefix):
    """פונקציה ראשית ליצירת חלקי פאזל קלאסיים.
    image_input: נתיב לקובץ תמונה (str) או אובייקט PIL Image
    """
    if isinstance(image_input, str):
        im = Image.open(image_input).convert("RGBA")
    else:
        im = image_input.convert("RGBA")

    arcRatio = DEFAULT_ARC_RATIO
    connectRatio = DEFAULT_CONNECT_RATIO
    # רדיוס הנקודות סקלבילי לפי גודל התמונה
    r = max(2, int(min(im.size[0], im.size[1]) / 500))

    info = PieceInfo(im.size, rows, cols, arcRatio, connectRatio)
    outLine = PieceOutLine(im.size[0] / cols, im.size[1] / rows, arcRatio, connectRatio)

    w = im.size[0] / cols
    h = im.size[1] / rows

    outLinePoints = []

    for i in range(rows):
        for j in range(cols):
            rect, center, borders = info.getPieceInfo(i, j)
            name = f"{output_prefix}{i}_{j}"

            region = im.crop(rect)
            curvPoints = outLine.genOutLine(borders)

            cropPoints = [(p[0] + center[0], p[1] + center[1]) for p in curvPoints]
            polygonCropImage(region, cropPoints, f"{name}.png")

            for p in curvPoints:
                outLinePoints.append((p[0] + j * w + 0.5 * w,
                                      p[1] + i * h + 0.5 * h))

    # שמירת תמונת outline ריקה
    outline_empty = Image.new('RGBA', im.size, (255, 255, 255, 0))
    outLinedraw = ImageDraw.Draw(outline_empty)

    for p in outLinePoints:
        px, py = p
        outLinedraw.ellipse((px - r, py - r, px + r, py + r),
                            fill=(0, 0, 0, 255), outline=(0, 0, 0, 255))

    outline_empty.save(f"{output_prefix}outline_only.png")

    # יצירת outline עם התמונה
    outline_with_image = im.copy()
    outLinedraw = ImageDraw.Draw(outline_with_image)

    for p in outLinePoints:
        px, py = p
        outLinedraw.ellipse((px - r, py - r, px + r, py + r),
                            fill=(0, 0, 0, 255), outline=(0, 0, 0, 255))

    outline_with_image.save(f"{output_prefix}outline_with_image.png")

    return outline_with_image


def create_rectangular_pieces(image_input, rows, cols, output_prefix):
    """יצירת חלקי פאזל מלבניים פשוטים.
    image_input: נתיב לקובץ תמונה (str) או אובייקט PIL Image
    """
    if isinstance(image_input, str):
        image = Image.open(image_input).convert("RGBA")
    else:
        image = image_input.convert("RGBA")

    width, height = image.size
    # חלוקה עם float לכיסוי מלא של הפיקסלים
    piece_width = width / cols
    piece_height = height / rows

    for i in range(rows):
        for j in range(cols):
            left = round(j * piece_width)
            top = round(i * piece_height)
            right = round((j + 1) * piece_width)
            bottom = round((i + 1) * piece_height)

            piece = image.crop((left, top, right, bottom))
            draw = ImageDraw.Draw(piece)
            draw.rectangle([(0, 0), (right - left - 1, bottom - top - 1)],
                           outline=(0, 0, 0), width=2)

            piece.save(f"{output_prefix}{i}_{j}.png")

    # יצירת תמונת outline עם התמונה
    preview = image.copy()
    draw = ImageDraw.Draw(preview)

    for i in range(rows + 1):
        y = round(i * piece_height)
        draw.line([(0, y), (width, y)], fill=(0, 0, 0), width=2)

    for j in range(cols + 1):
        x = round(j * piece_width)
        draw.line([(x, 0), (x, height)], fill=(0, 0, 0), width=2)

    preview.save(f"{output_prefix}outline_with_image.png")

    # יצירת גרסה ריקה עם קווים בלבד
    empty_preview = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(empty_preview)

    for i in range(rows + 1):
        y = round(i * piece_height)
        draw.line([(0, y), (width, y)], fill=(0, 0, 0), width=2)

    for j in range(cols + 1):
        x = round(j * piece_width)
        draw.line([(x, 0), (x, height)], fill=(0, 0, 0), width=2)

    empty_preview.save(f"{output_prefix}outline_only.png")

    return preview
