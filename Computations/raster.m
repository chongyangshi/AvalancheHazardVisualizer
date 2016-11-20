SOURCE_RASTER = '/media/icydoge/Shared/OS5/MATLAB/BNG.tif';
TARGET_RASTER = '/media/icydoge/Shared/OS5/MATLAB/BNGFitted.tif';
%ASPECT_RASTER = '/media/icydoge/Shared/OS5/MATLAB/BNGAspects.tif';

% Disable warnings.
%parpool;
%pctRunOnAll warning off;

% Read input raster and initialize.
[rst, raster_info] = geotiffread(SOURCE_RASTER);
x_list = 1:size(rst,1);
y_list = 1:size(rst,2);
x_max = size(x_list,2) - 1;
y_max = size(y_list,2) - 1;
output = rst;
%aspects = zeros(size(rst));

% Start timer.
disp('Surface fittings started...');
tic;

% Use: z = ax^2 + by^2 + cxy + dx + ey + f
% 
% (-1,1)  (0,1)  (1,1)
% (-1,0)  (0,0)  (1,0)
% (-1,-1) (0,-1) (1,-1)
%
coords = [-1 1; 0 1; 1 1; -1 0; 0 0; 1 0; -1 -1; 0 -1; 1 -1];
A(:,1) = coords(:,1).^2;
A(:,2) = coords(:,2).^2;
A(:,3) = coords(:,1).*coords(:,2);
A(:,4) = coords(:,1);
A(:,5) = coords(:,2);
A(:,6) = 1;

% Find neighbours of each point that is not on an edge, and choose the
% points that have all valid neighbours (non-zero), fit a surface for the
% neighbourhood and move the point onto the surface.
parfor_progress(x_max);
for x = 2:x_max
    %ux = sym('ux');
    %uy = sym('uy');
    for y = 2:y_max
        neighbours = pickneighbours(rst, x, y);
        if (any(isnan(neighbours(:))) == 0) && (any(neighbours(:,3)) == 1) % Check that boundaries are valid and no data is 0 (no-data in raster).
            z = neighbours(:,3);
            C = A\z;
            output(x,y) = C(6);
            
            % Differentiate to compute gradients and therefore surface
            % normal
            % From normal, infer aspect
            % Aspect = atan2(ny,nx);
            % Slope angle will be to do with nz, theta = acos(nz);
            % ... curvature, convexity...
            % The following (aspect calculation makes this ten times
            % slower when ran:
            %{
            equation = C(1) * ux^2 + C(2) * uy^2 + C(3) * ux * uy + C(4) * ux + C(5) * uy + C(6);
            dx = diff(equation, ux);
            dy = diff(equation, uy);
            nx = -1 / single(subs(dx, [ux, uy], [0 0]));
            ny = -1 / single(subs(dy, [ux, uy], [0 0]));
            aspects(x, y) = rad2deg(atan2(ny, nx)); 
            %}
            
            
        end
        
    end
    parfor_progress;
end

parfor_progress(0);

% Stop timer and report performance.
seconds = toc;
fprintf('Surface fitting completed in %f seconds.\r', seconds);
disp('Writing output to the target rasters...');

% Write output rasters.
CoordRefSysCode = 27700; % British National Grid.
geotiffwrite(TARGET_RASTER, output, raster_info, 'CoordRefSysCode', CoordRefSysCode);
disp('Output written to the target raster, all done.');
%geotiffwrite(ASPECT_RASTER, aspects, raster_info, 'CoordRefSysCode', CoordRefSysCode);
%disp('Output written to the aspect raster, all done.');

% Close off.
% delete(gcp('nocreate'));
