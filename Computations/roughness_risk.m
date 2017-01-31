function[risk, normalization] = roughness_risk(slopes, aspects)
%Requires a window of 9.
slopes(slopes<0) = 0;
aspects(aspects<0) = 0;
%Veitinger and Sovilla, 2016
zs = cosd(slopes);
dxys = sind(slopes);
xs = dxys .* cosd(aspects);
ys = dxys .* sind(aspects);
modr = sqrt(sum(xs).^2 + sum(ys).^2 + sum(zs).^2);
R = 1 - modr / 9;
fun = @(x) 1./(1+((x+0.005)./0.01).^4);
risk = fun(R);
normalization = 0.0222; % integral(fun, -Inf, Inf);