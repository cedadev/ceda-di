arsf-geo-map would benefit from various refactorings to be a good basis upon which to build a general data search system.  These notes specify where to start.  It is written from the perspective of CEDA and JASMIN as a whole.

 :Author: Stephen Pascoe

## Rename the repository.  

arsf-geo-map draws the remit of this package too narrowly.  The initial project is for EUFAR (which includes several data streams including ARSF) but we hope this software will ultimately be useful for datasets completely unrelated to ARSF.  Also it isn't just about driving a map.  Temporal, parameter-space and free-text searches are more important for some types of data.

I suggest renaming the repository to "ceda-di" for "CEDA Data Index".  We may change the brand name in the future.  We will probably spin out the web application into a separate repository in the future with a different name.

## Use Python packaging stucture

We need a setup.py and the package namespace needs renaming.  "eufar" should be renamed to ceda_dis (or to match the package name).  The config directory inside src needs either moving inside a package or outside src so that all directories in src represent python packages.

main.py needs moving inside the package hierarchy as a callable function.  Create an entry-point in setup.py.

## Refactor to enable easy addition of other file formats and metadata modules

We need a clear API for extending the list of file formats that are supported.  Similarly we need to be able to extend the categories of metadata which are added to ElasticSearch.

eufar.metadata.product.Properties holds more than just geospatial metadata (as the docstring describes).  This class needs to be extensible to add extra dicts (maybe these dicts need to be instances implementing an interface?).  It could probably be named better (Parameters/Parameter?)


