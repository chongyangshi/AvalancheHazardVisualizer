function[risk, normalization] = slope_risk(x)
fun = @(n) 1./(1+((n-42.5)./8).^6);
risk = fun(x);
normalization = 16.7552; % integral(fun, -Inf, Inf);