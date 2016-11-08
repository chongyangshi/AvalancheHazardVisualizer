SOURCE_RASTER = 'NM98NESEAspects.tif';
TARGET_RASTER = 'NM98NESEAspectsFitted.tif';

% Disable warnings.
pctRunOnAll warning off;

% Read input raster and initialize.
[rst, raster_info] = geotiffread(SOURCE_RASTER);
x_list = 1:size(rst,1);
y_list = 1:size(rst,2);
x_max = size(x_list,2) - 1;
y_max = size(y_list,2) - 1;
output = zeros(size(x_list, 2), size(y_list, 2));

% Find neighbours of each point that is not on an edge, and choose the
% points that have all valid neighbours (non-zero), fit a surface for the
% neighbourhood and move the point onto the surface.
parfor x = 2:x_max
    for y = 2:y_max
        neighbours = pickneighbours(rst, x, y);
        if (any(isnan(neighbours(:))) == 0) && (any(neighbours(:,3)) == 1) % Check that boundaries are valid and no data is 0 (no-data in raster).
            surface_fitted = fit([neighbours(:,1), neighbours(:,2)], neighbours(:,3), 'poly22');
            output(x,y) = surface_fitted(x,y);
        end
    end
end

% Write output raster.
CoordRefSysCode = 27700;
geotiffwrite(TARGET_RASTER, output, raster_info, 'CoordRefSysCode', CoordRefSysCode);

% Re-enable warnings.
pctRunOnAll warning on;