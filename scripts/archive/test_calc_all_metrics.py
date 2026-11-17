import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import math
import time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.io
import scipy.ndimage
import scipy.special
import scipy.linalg
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr_fn
from skimage.metrics import structural_similarity as ssim_fn
from skimage.metrics import mean_squared_error as mse_fn
import torch
import torchvision.transforms.functional as TF
import lpips
from pytorch_fid.inception import InceptionV3
from pytorch_fid.fid_score import calculate_activation_statistics

# 1. NIQE setup
mat_path = Path(r'C:/Users/ankit/AppData/Roaming/Python/Python314/site-packages/skvideo/measure/data/niqe_image_params.mat')
params = scipy.io.loadmat(mat_path)
pop_mu = np.ravel(params['pop_mu'])
pop_cov = params['pop_cov']

gamma_range = np.arange(0.2, 10.0, 0.001)
gam1_arr = scipy.special.gamma(1.0 / gamma_range)
gam2_arr = scipy.special.gamma(2.0 / gamma_range)
gam3_arr = scipy.special.gamma(3.0 / gamma_range)
prec_gammas = (gam2_arr ** 2) / (gam1_arr * gam3_arr)

def gen_gauss_window(lw=3, sigma=7.0/6.0):
    weights = [0.0] * (2 * lw + 1)
    weights[lw] = 1.0
    sum_w = 1.0
    sd_sq = sigma * sigma
    for ii in range(1, lw + 1):
        tmp = math.exp(-0.5 * (ii * ii) / sd_sq)
        weights[lw + ii] = tmp
        weights[lw - ii] = tmp
        sum_w += 2.0 * tmp
    return [w / sum_w for w in weights]

AVG_WINDOW = gen_gauss_window()

def compute_image_mscn_transform(image):
    h, w = image.shape
    mu_image = np.zeros((h, w), dtype=np.float32)
    var_image = np.zeros((h, w), dtype=np.float32)
    scipy.ndimage.correlate1d(image, AVG_WINDOW, 0, mu_image, mode='constant')
    scipy.ndimage.correlate1d(mu_image, AVG_WINDOW, 1, mu_image, mode='constant')
    scipy.ndimage.correlate1d(image**2, AVG_WINDOW, 0, var_image, mode='constant')
    scipy.ndimage.correlate1d(var_image, AVG_WINDOW, 1, var_image, mode='constant')
    var_image = np.sqrt(np.maximum(var_image - mu_image**2, 0.0))
    return (image - mu_image) / (var_image + 1.0)

def aggd_features(imdata):
    flat = imdata.ravel()
    imdata2 = flat * flat
    left_data = imdata2[flat < 0]
    right_data = imdata2[flat >= 0]
    left_mean_sqrt = np.sqrt(np.mean(left_data)) if len(left_data) > 0 else 0.0
    right_mean_sqrt = np.sqrt(np.mean(right_data)) if len(right_data) > 0 else 0.0

    gamma_hat = left_mean_sqrt / right_mean_sqrt if right_mean_sqrt != 0 else np.inf
    imdata2_mean = np.mean(imdata2)
    r_hat = (np.mean(np.abs(flat)) ** 2) / imdata2_mean if imdata2_mean != 0 else np.inf
    
    if math.isinf(gamma_hat) or math.isinf(r_hat):
        rhat_norm = np.inf
    else:
        rhat_norm = r_hat * (((gamma_hat**3 + 1) * (gamma_hat + 1)) / ((gamma_hat**2 + 1) ** 2))

    pos = int(np.argmin((prec_gammas - rhat_norm)**2))
    alpha = gamma_range[pos]
    gam1 = gam1_arr[pos]
    gam2 = gam2_arr[pos]
    gam3 = gam3_arr[pos]
    aggdratio = np.sqrt(gam1) / (np.sqrt(gam3) + 1e-7)
    bl = aggdratio * left_mean_sqrt
    br = aggdratio * right_mean_sqrt
    N = (br - bl) * (gam2 / (gam1 + 1e-7))
    return alpha, N, bl, br

def _niqe_extract_subband_feats(mscncoefs):
    alpha_m, N_m, bl_m, br_m = aggd_features(mscncoefs)
    shift1 = np.roll(mscncoefs, 1, axis=1)
    shift2 = np.roll(mscncoefs, 1, axis=0)
    shift3 = np.roll(np.roll(mscncoefs, 1, axis=0), 1, axis=1)
    shift4 = np.roll(np.roll(mscncoefs, 1, axis=0), -1, axis=1)
    
    a1, n1, bl1, br1 = aggd_features(shift1 * mscncoefs)
    a2, n2, bl2, br2 = aggd_features(shift2 * mscncoefs)
    a3, n3, bl3, br3 = aggd_features(shift3 * mscncoefs)
    a4, n4, bl4, br4 = aggd_features(shift4 * mscncoefs)
    
    return [
        alpha_m, (bl_m + br_m) / 2.0,
        a1, n1, bl1, br1,
        a2, n2, bl2, br2,
        a3, n3, bl3, bl3,
        a4, n4, bl4, bl4,
    ]

def extract_on_patches(img, patch_size):
    h, w = img.shape
    patch_size = int(patch_size)
    patch_features = []
    for j in range(0, h - patch_size + 1, patch_size):
        for i in range(0, w - patch_size + 1, patch_size):
            patch = img[j:j+patch_size, i:i+patch_size]
            patch_features.append(_niqe_extract_subband_feats(patch))
    return np.array(patch_features)

def calculate_niqe(img_gray):
    img = np.asarray(img_gray, dtype=np.float32)
    h, w = img.shape
    patch_size = 96
    hoffset = h % patch_size
    woffset = w % patch_size
    if hoffset > 0:
        img = img[:-hoffset, :]
    if woffset > 0:
        img = img[:, :-woffset]
        
    pil_im = Image.fromarray(img)
    img2 = np.array(pil_im.resize((img.shape[1] // 2, img.shape[0] // 2), resample=Image.BICUBIC), dtype=np.float32)
    
    mscn1 = compute_image_mscn_transform(img)
    mscn2 = compute_image_mscn_transform(img2)
    
    feats_lvl1 = extract_on_patches(mscn1, patch_size)
    feats_lvl2 = extract_on_patches(mscn2, patch_size // 2)
    
    feats = np.hstack((feats_lvl1, feats_lvl2))
    sample_mu = np.mean(feats, axis=0)
    sample_cov = np.cov(feats.T)
    
    X = sample_mu - pop_mu
    covmat = (pop_cov + sample_cov) / 2.0
    pinvmat = scipy.linalg.pinv(covmat)
    score = np.sqrt(np.dot(np.dot(X, pinvmat), X))
    return float(score)

def calculate_frechet_distance_custom(mu1, sigma1, mu2, sigma2, eps=1e-6):
    diff = mu1 - mu2
    covmean = scipy.linalg.sqrtm(sigma1.dot(sigma2))
    if not np.isfinite(covmean).all():
        offset = np.eye(sigma1.shape[0]) * eps
        covmean = scipy.linalg.sqrtm((sigma1 + offset).dot(sigma2 + offset))
    if np.iscomplexobj(covmean):
        covmean = covmean.real
    return float(diff.dot(diff) + np.trace(sigma1) + np.trace(sigma2) - 2 * np.trace(covmean))

def main():
    PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
    meta_path = PROJECT_ROOT / "datasets" / "processed" / "metadata" / "cyclegan_generated_metadata.csv"
    real_fog_dir = PROJECT_ROOT / "datasets" / "cyclegan" / "fog"
    
    meta_df = pd.read_csv(meta_path)
    print(f"Loaded {len(meta_df)} generated records.")
    
    day_sample = meta_df[meta_df["source_domain"] == "day"].head(100)
    night_sample = meta_df[meta_df["source_domain"] == "night"].head(100)
    
    lpips_model = lpips.LPIPS(net="alex", verbose=False)
    
    def process_subset(sub_df, domain_name):
        results = []
        batch_src = []
        batch_gen = []
        
        t0 = time.time()
        for i, (_, row) in enumerate(sub_df.iterrows()):
            src_img = Image.open(row["source_path"]).convert("RGB").resize((256, 256))
            gen_img = Image.open(row["generated_path"]).convert("RGB")
            
            src_arr = np.array(src_img)
            gen_arr = np.array(gen_img)
            
            v_mse = float(mse_fn(src_arr, gen_arr))
            v_mae = float(np.mean(np.abs(src_arr.astype(np.float32) - gen_arr.astype(np.float32))))
            v_psnr = float(psnr_fn(src_arr, gen_arr, data_range=255))
            v_ssim = float(ssim_fn(src_arr, gen_arr, channel_axis=2, data_range=255))
            v_niqe = float(calculate_niqe(gen_img.convert("L")))
            
            batch_src.append(TF.to_tensor(src_img) * 2.0 - 1.0)
            batch_gen.append(TF.to_tensor(gen_img) * 2.0 - 1.0)
            
            results.append({
                "mse": v_mse,
                "mae": v_mae,
                "psnr": v_psnr,
                "ssim": v_ssim,
                "niqe": v_niqe,
            })
            
            if len(batch_src) == 32 or i == len(sub_df) - 1:
                with torch.no_grad():
                    d_lpips = lpips_model(torch.stack(batch_src), torch.stack(batch_gen)).squeeze().cpu().numpy()
                if np.ndim(d_lpips) == 0:
                    d_lpips = [float(d_lpips)]
                else:
                    d_lpips = [float(v) for v in d_lpips]
                for r_idx, l_val in zip(range(i - len(d_lpips) + 1, i + 1), d_lpips):
                    results[r_idx]["lpips"] = l_val
                batch_src = []
                batch_gen = []
                
        df_res = pd.DataFrame(results)
        print(f"\n--- {domain_name} ({len(sub_df)} samples, {time.time()-t0:.1f}s) ---")
        for col in ["psnr", "ssim", "mse", "mae", "lpips", "niqe"]:
            print(f"  {col.upper():<6}: Mean={df_res[col].mean():.4f}, Median={df_res[col].median():.4f}, Std={df_res[col].std():.4f}")
        return df_res

    res_day = process_subset(day_sample, "Day->Fog")
    res_night = process_subset(night_sample, "Night->Fog")

    # Now calculate FID on real fog vs day fog and night fog
    print("\nComputing InceptionV3 activation statistics for FID...")
    device = torch.device("cpu")
    block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[2048]
    inception = InceptionV3([block_idx]).to(device)
    
    valid_ext = {".jpg", ".jpeg", ".png"}
    real_files = sorted([p for p in real_fog_dir.iterdir() if p.suffix.lower() in valid_ext])
    day_files = [Path(p) for p in day_sample["generated_path"]]
    night_files = [Path(p) for p in night_sample["generated_path"]]
    
    m_real, s_real = calculate_activation_statistics(real_files, inception, batch_size=25, dims=2048, device=device, num_workers=0)
    m_day, s_day = calculate_activation_statistics(day_files, inception, batch_size=25, dims=2048, device=device, num_workers=0)
    m_night, s_night = calculate_activation_statistics(night_files, inception, batch_size=25, dims=2048, device=device, num_workers=0)
    
    fid_day = calculate_frechet_distance_custom(m_real, s_real, m_day, s_day)
    fid_night = calculate_frechet_distance_custom(m_real, s_real, m_night, s_night)
    
    print(f"\nFID Scores (vs Real Fog baseline, N={len(real_files)}):")
    print(f"  Day->Fog FID:   {fid_day:.3f}")
    print(f"  Night->Fog FID: {fid_night:.3f}")

if __name__ == "__main__":
    main()
