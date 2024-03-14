clc; close all; clear;

% Determine where your m-file's folder is.
folder = fileparts(which(mfilename("fullpath"))); 
% Add that folder plus all subfolders to the path.
addpath(genpath(folder));

mkdir("output");
mkdir(fullfile("output", "chl"));
mkdir(fullfile("output", "png"));

%% hdr paramters
DimsHWN     = [956,684,120];
precision   = "uint16";
offset      = 0;
interleave  = "bip";
byteorder   = 'ieee-le';

% for spectra analysis
function_name = "br_549_over_663";

spectral_coeffs = [ -5.719788129534360902e-09 
                    1.324037080791479811e-05 
                    3.751455956374321055e-01
                    2.264762366937773663e+02];
x_start = 428;
x_stop = 1508;
image_width = 120;
x = linspace(x_start, x_stop, image_width);
h1_wl = spectral_coeffs(4) + ...
        spectral_coeffs(3).*x + ...
        spectral_coeffs(2).*x.*x + ...
        spectral_coeffs(1).*x.*x.*x;

[~, R] = min(abs(h1_wl-665));
[~, G] = min(abs(h1_wl-540));
[~, B] = min(abs(h1_wl-470));

%% read
top_folder_name = "Svalbard";
listing = dir(top_folder_name);

counter = 0;
for ii = 1:length(listing)
    folder_name = listing(ii).name;
    date = split(listing(ii).name,"_");

    if not(contains(date{1},"2022"))
        continue
    end

    full_folder_name = fullfile(top_folder_name, folder_name);
    folder_content = dir(full_folder_name);

    png_li = {};
    for jj = 1:length(folder_content)
        if endsWith(folder_content(jj).name, ".bip")
            filename_cube = folder_content(jj).name;
        elseif endsWith(folder_content(jj).name, ".png")
            png_li{end+1} = string(folder_content(jj).name);
        end
    end

    if length(png_li) > 1
        for e = 1:length(png_li)
            if contains(png_li{e},"bin3")
                filename_png = png_li{e};
            end
        end
    elseif length(png_li) == 1
        filename_png = png_li{1};
    end
    
    filename_png = fullfile(full_folder_name, filename_png);
    I_png = imread(filename_png);
    
    if size(I_png,1) < size(I_png,2)
        I_png = rot90(I_png,3);
    end

    h = imshow(I_png,"Border","tight");
    
    dim = [0.01 .7 0 0.3];
    str = date(1);
    annotation('textbox',dim,'String',str,'FitBoxToText','on');

    exportgraphics(gca,fullfile("output", "png", ...
    sprintf("svalbard_%s_%s.png",date{1},string(counter))),...
    "Resolution",400);

    filename_cube = fullfile(full_folder_name, filename_cube);
    [h1_data] = read_cube(filename_cube, ...
       DimsHWN, precision, offset, interleave, byteorder);

    chlor = get_c(h1_data, h1_wl, function_name);

    % Relative treshold on results
    chlor = chlor - .88*max(chlor(:));
    chlor(chlor < 0) = 0;
    
    h1_data_dim = [size(I_png,1),size(I_png,2)];

    % Make it green
    I_chlor = imresize(chlor, h1_data_dim(1:2));    
    X = zeros(size(I_chlor,1), size(I_chlor,2), 3);
    X(:,:,2) = I_chlor;
    
    I_alph = im2uint8(X) + I_png; 
    imshow(I_alph,"Border","tight");

    exportgraphics(gca,fullfile("output", "chl",...
    sprintf("svalbard_%s_%s.png",date{1},string(counter))),...
    "Resolution",600);


    counter = counter + 1;
    break;
end

function [cube] = read_cube(fname, DimsHWN, precision, offset, interleave, byteorder)
cube = multibandread(fname,DimsHWN,precision,offset,interleave,byteorder);
cube = flip(cube,3);

%h1_data_dim = [956,150,120];
%h1_data = zeros(h1_data_dim);
%
%for i = 1:size(cube,3)
%    h1_data(:,:,i) = imresize(cube(:,:,i), h1_data_dim(1:2));
%end

end

function [c_img] = get_c(h1_data, h1_wl, function_name)
    c_img = zeros(size(h1_data,1), size(h1_data,2));

    for xx = 1:size(h1_data,1)
        for yy = 1:size(h1_data,2)
            spectra = squeeze(h1_data(xx,yy,:));
            c_img(xx,yy) = feval(function_name,spectra, h1_wl);
        end
    end
end

function [result] = br_549_over_663(spectra,h1_wl)
    [~, C1] = min(abs(h1_wl-549));
    [~, C2] = min(abs(h1_wl-663));
    
    result = spectra(C1)/spectra(C2);
end

%
% TEMPLATE FUNCTION
%
% function [result] = function_name(spectra,h1_wl)
%     [~, index] = min(abs(h1_wl-Desired_wavlength_in_nanometers));
%     
%     result = % what you want to do with the spectra
% end