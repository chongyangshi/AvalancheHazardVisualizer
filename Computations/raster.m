SOURCE_RASTER = 'NM98NWAspects.tif';
TARGET_RASTER = 'NM98NWAspectsFitted.tif';

% Disable warnings.
warning off;

% Read input raster and initialize.
[rst, raster_info] = geotiffread(SOURCE_RASTER);
x_list = 1:size(rst,1);
y_list = 1:size(rst,2);
output = zeros(size(x_list, 2), size(y_list, 2));
num_processed = 0;

% Find neighbours of each point that is not on an edge, and choose the
% points that have all valid neighbours (non-zero), fit a surface for the
% neighbourhood and move the point onto the surface.
for x = 2:(size(x_list,2)-1)
    for y = 2:(size(y_list,2)-1)
        neighbours = pickneighbours(rst, x, y);
        if (any(isnan(neighbours(:))) == 0) && (any(neighbours(:,3)) == 1) % Check that boundaries are valid and no data is 0 (no-data in raster).
            surface_fitted = fit([neighbours(:,1), neighbours(:,2)], neighbours(:,3), 'poly22');
            output(x,y) = surface_fitted(x,y);
        end
        num_processed = num_processed + 1;
        fprintf( 'Processed: %d\r\n', num_processed );
    end
end

% Write output raster.
geotiffwrite(TARGET_RASTER, output, raster_info);

% Re-enable warnings.
warning on;