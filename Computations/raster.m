SOURCE_RASTER = '~/Documents/NN2627.tif';
TARGET_RASTER = '~/Documents/NN2627Fitted.tif';

% Disable warnings.
parpool;
pctRunOnAll warning off;

% Read input raster and initialize.
[rst, raster_info] = geotiffread(SOURCE_RASTER);
x_list = 1:size(rst,1);
y_list = 1:size(rst,2);
x_max = size(x_list,2) - 1;
y_max = size(y_list,2) - 1;
output = rst;

% Start timer.
disp('Surface fittings started...');
tic;

% Find neighbours of each point that is not on an edge, and choose the
% points that have all valid neighbours (non-zero), fit a surface for the
% neighbourhood and move the point onto the surface.
parfor x = 2:x_max
    for y = 2:y_max
        neighbours = pickneighbours(rst, x, y);
        if (any(isnan(neighbours(:))) == 0) && (any(neighbours(:,3)) == 1) % Check that boundaries are valid and no data is 0 (no-data in raster).
            surface_fitted = fit([neighbours(:,1), neighbours(:,2)], neighbours(:,3), 'poly22');
            % Differentiate to compute gradients and therefore surface
            % normal
            % From normal, infer aspect
            % Aspect = atan2(ny,nx);
            % Slope angle will be to do with nz, theta = acos(nz);
            % ... curvature, convexity...
            output(x,y) = surface_fitted(x,y);
        end
    end
end

% Stop timer and report performance.
seconds = toc;
fprintf('Surface fitting completed in %f seconds.\r', seconds);
disp('Writing output to the target raster...');

% Write output raster.
CoordRefSysCode = 27700;
geotiffwrite(TARGET_RASTER, output, raster_info, 'CoordRefSysCode', CoordRefSysCode);
disp('Output written to the target raster, all done.');

% Re-enable warnings.
pctRunOnAll warning on;