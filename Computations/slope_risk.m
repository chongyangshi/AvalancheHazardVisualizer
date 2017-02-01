function[risk] = slope_risk(x)
val = 1./(1+((x-42.5)./8).^6);
risk = val ./ 16.7552; % integral(fun, -Inf, Inf);