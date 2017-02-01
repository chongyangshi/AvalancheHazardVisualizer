function[risk] = curvature_risk(x)
val = x.^3 + 0.5;
val(val > 1) = 1;
val(val < 0) = 0;
risk = abs(val) ./ 0.7937;