function[risk] = curvature_risk(x)
lower = -0.79;
upper = 0.79;
if (lower <= x) && (x <= upper)
    risk = x.^3 + 0.5;
elseif (x < lower)
    risk = 0;
else
    risk = 1;
end;