function[risk, normalization] = curvature_risk(x)
risk = curvature_calc(x);
normalization = 0.7937 + (max(abs(x), 0.7937) - 0.7937);

function[val] = curvature_calc(n)
n(n < -0.79) = 0;
n(n > 0.79) = 0.7937; % 0.7937^3 + 0.5 ~= 1
val = n.^3 + 0.5;