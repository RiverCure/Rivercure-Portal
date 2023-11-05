import argparse as arg
import ogr
import os


def createBuffer(inputfn, outputBufferfn, bufferDist):
    inputds = ogr.Open(inputfn)
    inputlyr = inputds.GetLayer()

    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(outputBufferfn):
        shpdriver.DeleteDataSource(outputBufferfn)
    outputBufferds = shpdriver.CreateDataSource(outputBufferfn)
    bufferlyr = outputBufferds.CreateLayer(
        outputBufferfn, geom_type=ogr.wkbPolygon)
    featureDefn = bufferlyr.GetLayerDefn()

    for feature in inputlyr:
        ingeom = feature.GetGeometryRef()
        geomBuffer = ingeom.Buffer(bufferDist)

        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(geomBuffer)
        bufferlyr.CreateFeature(outFeature)
        outFeature = None


if __name__ == "__main__":
    parser = arg.ArgumentParser(description='Optional app description')
    parser.add_argument('-i', '--input',
                        type=str,
                        required=True,
                        help='path to input domain.geojson to use to cut')
    parser.add_argument('-o', '--output',
                        type=str,
                        required=True,
                        help='path to tiff to use as buffer')
    parser.add_argument('-d', '--distance',
                        type=float,
                        required=True,
                        help='buffer distance')
    args = parser.parse_args()

    createBuffer(args.input, args.output, args.distance)
