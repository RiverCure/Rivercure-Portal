#!/usr/bin/env python3

# usage: python3 pyResults.py -i [input.vtk file] -o [output.tif file]
#        -r [.tif resolution] -q [quantities to convert] -e [epsg]

import argparse as arg
import numpy as np
import matplotlib.pyplot as plt
from vtk import vtkUnstructuredGridReader
from vtk.util import numpy_support as vn
from scipy.interpolate import griddata
from osgeo import gdal
from osgeo import osr


class barycenter:

    def __init__(self):
        self.x = 0.0
        self.y = 0.0


class geoRaster:

    def __init__(self):
        self.res = 0.0
        self.lines = 0
        self.cols = 0
        self.xmin = np.math.inf
        self.ymax = -np.math.inf
        self.x = None
        self.y = None
        self.max = None
        self.epsg = 3857
        self.filename = None

    def writeTIFF(self, quantity):
        geoTransform = (self.xmin, self.res, 0, self.ymax, 0, -self.res)
        outFile = self.filename + '-' + quantity + '.tif'
        tiffWritter = gdal.GetDriverByName('GTiff').Create(outFile, self.cols, self.lines, 1, gdal.GDT_Float32)
        tiffWritter.SetGeoTransform(geoTransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(self.epsg)
        tiffWritter.SetProjection(srs.ExportToWkt())
        tiffWritter.GetRasterBand(1).WriteArray(self.max)
        tiffWritter.FlushCache()


def main():

    # parse command line
    parser = arg.ArgumentParser(description='Optional app description')
    parser.add_argument('-i', '--input',
                        type=arg.FileType('r'),
                        required=True,
                        help='input maxi-*.vtk to read')
    parser.add_argument('-o', '--output',
                        type=str,
                        required=True,
                        default='out',
                        help='output .tiff to write (w/o extension)')
    parser.add_argument('-r', '--resolution',
                        type=float,
                        default=30.0,
                        help='raster resolution (default: 30.0)')
    parser.add_argument('-q', '--quantity',
                        type=str,
                        default='all',
                        help='specified quantity only (default: all)')
    parser.add_argument('-e', '--epsg',
                        type=int,
                        default=3857,
                        help='EPSG code for output CRS (default: 3857)')
    parser.add_argument('-s', '--show',
                        action='store_true',
                        help='show tiff')
    args = parser.parse_args()
    if args.quantity != 'all':
        quantities = np.array([args.quantity])
    else:
        quantities = np.array(['Max_Depth', 'Max_Level', 'Max_Vel', 'Max_Q'])

    # read the source file with VTK API
    reader = vtkUnstructuredGridReader()
    reader.SetFileName(args.input.name)
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()
    output = reader.GetOutput()

    # copy raw data as numpy arrays
    # mesh data
    pts = vn.vtk_to_numpy(output.GetPoints().GetData())
    cells2pts = vn.vtk_to_numpy(output.GetCells().GetData())
    numVols = int(cells2pts.size/4)
    cells2pts = np.reshape(cells2pts, (numVols, 4))
    cells2pts = cells2pts[:, 1:]
    cellCenters = np.array([barycenter() for v in range(numVols)])

    # set bounding box
    minX = np.math.inf
    minY = np.math.inf
    maxX = -np.math.inf
    maxY = -np.math.inf

    volIdx = 0
    for c in cellCenters:
        c.x = 1/3 * (pts[cells2pts[volIdx, 0], 0] + pts[cells2pts[volIdx, 1], 0] + pts[cells2pts[volIdx, 2], 0])
        c.y = 1/3 * (pts[cells2pts[volIdx, 0], 1] + pts[cells2pts[volIdx, 1], 1] + pts[cells2pts[volIdx, 2], 1])
        if c.x < minX:
            minX = c.x
        if c.y < minY:
            minY = c.y
        if c.x > maxX:
            maxX = c.x
        if c.y > maxY:
            maxY = c.y
        volIdx = volIdx + 1

    outRaster = geoRaster()
    outRaster.res = args.resolution
    outRaster.xmin = minX
    outRaster.ymax = maxY
    xVec = np.linspace(minX, maxX, int((maxX - minX) / outRaster.res))
    yVec = np.linspace(minY, maxY, int((maxY - minY) / outRaster.res))
    outRaster.lines = yVec.size
    outRaster.cols = xVec.size
    outRaster.filename = args.output
    outRaster.epsg = args.epsg
    outRaster.x, outRaster.y = np.meshgrid(xVec, yVec)

    x = np.array([c.x for c in cellCenters])
    y = np.array([c.y for c in cellCenters])
    xy = np.column_stack((x, y))
    xQ = np.reshape(outRaster.x, (1, yVec.size * xVec.size))
    yQ = np.reshape(outRaster.y, (1, yVec.size * xVec.size))

    for q in quantities:
        max = vn.vtk_to_numpy(output.GetCellData().GetArray(q))
        maxQ = griddata(xy, max, (xQ, yQ), method='nearest')
        maxQ = np.reshape(maxQ, (yVec.size, xVec.size))
        outRaster.max = np.flipud(maxQ)
        # plot images
        if args.show:
            plt.imshow(outRaster.max)
            plt.colorbar()
            plt.show()
        outRaster.writeTIFF(q)


if __name__ == '__main__':
    main()

    '''
    https://gis.stackexchange.com/questions/333914/how-to-clip-raster-inside-of-circle-python-gdal
    scalar_range = output.GetScalarRange()
    # Create the mapper that corresponds the objects of the vtk.vtk file
    # into graphics elements
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputData(output)
    mapper.SetScalarRange(scalar_range)
    mapper.ScalarVisibilityOff()

    # Create the Actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().EdgeVisibilityOn()

    # Create the Renderer
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(1, 1, 1)

    # Create the RendererWindow
    renderer_window = vtk.vtkRenderWindow()
    renderer_window.AddRenderer(renderer)

    # Create the RendererWindowInteractor and display the vtk_file
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renderer_window)
    interactor.Initialize()
    interactor.Start()
    '''
