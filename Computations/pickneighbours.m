function [neighbours] = pickneighbours(rst, x, y)
%Given a point in raster, create a matrix containing a column of x's, a
%column of y's and a column of z's representing the neighbours of point
%(x,y), as well as (x,y) itself at fifth location.

% Boundary validations.
if (x < 2) || (x > (size(rst, 1) - 1))
    neighbours = NaN;
    return
end

if (y < 2) || (y > (size(rst, 2) - 1))
    neighbours = NaN;
    return
end

neighbours = zeros(9,3);
current_position = 1;
for i = (x-1):(x+1)
    for j = (y-1):(y+1)
        neighbours(current_position,1) = i;
        neighbours(current_position,2) = j;
        neighbours(current_position,3) = rst(i,j);
        current_position = current_position + 1;
    end
end