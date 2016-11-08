SOURCE_RASTER = 'NM98NWAspects.tif';
[rst, raster_info] = geotiffread(SOURCE_RASTER);
x_list = linspace(raster_info.XWorldLimits(1), raster_info.XWorldLimits(2), raster_info.RasterSize(1));
y_list = linspace(raster_info.YWorldLimits(1), raster_info.YWorldLimits(2), raster_info.RasterSize(2));
x_laid_out = repmat(x_list', size(y_list, 2), 1);
y_laid_out = repmat(y_list', size(x_list, 2), 1);
xs = reshape(x_laid_out', numel(x_laid_out), 1);
ys = reshape(y_laid_out', numel(y_laid_out), 1);
raster_flattened = reshape(rst', numel(rst), 1);
sf = fit([xs, ys],raster_flattened, 'poly22');
plot(sf,[xs, ys],raster_flattened);