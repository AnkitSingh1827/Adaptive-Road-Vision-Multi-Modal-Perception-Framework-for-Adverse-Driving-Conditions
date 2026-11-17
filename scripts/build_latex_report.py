# Script to generate project_report.tex
import os
from pathlib import Path

tex_content = r"""\documentclass{article}
\usepackage{IEEEtrantools}
\usepackage[utf8]{inputenc}
\usepackage{wrapfig}
\usepackage{lscape}
\usepackage{rotating}
\usepackage{graphicx}
\usepackage{caption}
\usepackage{amsmath, nccmath, amssymb, amsfonts}
\usepackage{comment}
\usepackage{afterpage}
\usepackage{multirow}
\usepackage{multicol}
\usepackage{cleveref}
\usepackage{makecell}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{placeins}
\usepackage{adjustbox}
\usepackage{arydshln} % dashed midline
\usepackage{ragged2e}
\usepackage{lipsum}
\usepackage{mathtools} % To use box inside an aligned environment
\usepackage{enumitem}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\usepackage{cite}

\newcommand\myemptypage{
    \null
    \thispagestyle{empty}
    \addtocounter{page}{-1}
    \newpage
    }
%\pagenumbering{gobble}% Remove page numbers (and reset to 1)
\thispagestyle{empty}
\pagenumbering{arabic}
\begin{document}
%\newgeometry{centering,top = 2.54cm,bottom = 2.54cm,left = 2.54cm, right = 2.54cm, includeheadfoot}
\renewcommand{\thepage}{\roman{page}}
\begin{titlepage}
%\setlength{\voffset}{-0.1in}
%\setlength{\headsep}{5pt}
%\setlength{\textheight}{650pt}
%titlepage
%\thispagestyle{empty}
\begin{center}
%\begin{minipage}{0.75\linewidth}
    \centering
     
%=====================================================%
%---------------THESIS TITLE--------------------------%
%=====================================================%    
      
  {{\LARGE \textbf{Adaptive Road Vision: Multi-Modal Perception Framework for Adverse Driving Conditions}\par}}
    \vspace{0.1cm}% FOR CREATING DESIRED SPACE BETWEEN THE LINES
     
%=====================================================%
%---------------Partial Fulfillment---------------------%
%=====================================================%
    \vspace{1cm}
    {\Large \bf For\par}
    {\Large \bf Machine Learning for Predictive Analytics (CUML1021)  \par}
    \vspace{0.1cm}
   

%=====================================================%
%---------------AUTHOR'S NAME-------------------------%
%=====================================================%

    {\large \bf by\par}
    \vspace{0.5cm}
    {\large \textbf{{Ankit Singh (240301120081) }}\par} 
    {\large \textbf{{Naman Parashar (240301120089) }}\par}
    {\large \textbf{{Priyanka Priyadarshini Nayak (240301120094) }}\par}
    {\large \textbf{{Sonakshi Gupta (240301120098) }}\par}
    
%    {\Large \textbf{(2013MEZ8469)}\par}
    \vspace{0.4cm}
    
%=====================================================%
%---------------Supervisor Name-----------------------%
%=====================================================%    
%    {\Large \textbf{Doctor of Philosophy} \par}
%    \vspace{0.5cm}
    {\large Under the Supervision of \par}
    {\Large \textbf{{Dr. Sunil Kumar Mohapatra}}\par}
%    {\Large \textbf{(2013MEZ8469)}\par}
     \vspace{0.8 cm}

%=====================================================%
%---------------UNIVERSITY LOGO-----------------------%
%=====================================================%
\includegraphics[width=0.25\linewidth]{Screenshot 2026-10-12 094207.png}
%    \rule{0.4\linewidth}{0.15\linewidth}\par
     \vspace{0.3 cm}

    
%=====================================================%
%---------------DEPARTMENT'S NAME---------------------%
%=====================================================%   
    {\large \textbf{SCHOOL OF ENGINEERING AND TECHNOLOGY}\\
    {\large \textbf{BHUBANESWAR CAMPUS}}\par}
    \vspace{0.3cm}

    {\large \textbf{CENTURION UNIVERSITY OF TECHNOLOGY AND MANAGEMENT \\
    ODISHA}\par}
    \vspace{0.4cm}
       
    {\large \textbf{OCTOBER 2026}}
\end{center}
\end{titlepage}

\newpage
%\thispagestyle{empty}

\phantomsection
\addcontentsline{toc}{section}{Bonafide Certificate}

\begin{center}
    {\Large \textbf{DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING}}\\[0.35cm]
    {\large \textsc{School of Engineering and Technology}}\\
    {\large \textsc{Bhubaneswar Campus}}\\[0.8cm]

    {\LARGE \textbf{\underline{BONAFIDE CERTIFICATE}}}
\end{center}

\vspace{0.4cm}
\begin{justify}
\large Certified that this project report \textbf{``Adaptive Road Vision: Multi-Modal Perception Framework for Adverse Driving Conditions''} is the bonafide work of \textbf{Ankit Singh (240301120081), Naman Parashar (240301120089), Priyanka Priyadarshini Nayak (240301120094), and Sonakshi Gupta (240301120098)} who carried out the project work under my supervision. This is to certify that this project has not been carried out earlier in this institute and the university to the best of my knowledge.
\end{justify}

\vfill

\begin{flushright}
    \large
    \textbf{(Dr. Sunil Kumar Mohapatra)}\\
    Assoc. Professor(I), Dept. of CSE, SoET
\end{flushright}

\vfill

\noindent\textit{\large Certified that the project mentioned above has been duly carried out as per the college's norms and the university's statutes.}

\vfill
\vspace{0.5cm}

\noindent
\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}cc}
    \textbf{\large Dr. Swarna Prabha Jena} & \textbf{\large Dr. Rahul Ray} \\ 
    \large Associate Dean, SoET & \large HoD, Dept. of CSE, SoCDS \\
\end{tabular*}

\newpage

\vfill
\newpage
%\thispagestyle{empty}
\section*{} % unnumbered section not in ToC
\addcontentsline{toc}{section}{Declaration}
\begin{center}
\underline{\LARGE \textbf{DECLARATION}}\\[1.5cm]
\end{center}
\large{We hereby declare that the project entitled “Adaptive Road Vision: Multi-Modal Perception Framework for Adverse Driving Conditions” submitted for the “Project” of $5^{th}$ semester B. Tech in Computer Science
and Engineering our original work and the project has not formed the basis for the award of any Degree / Diploma or any other similar titles in any other University / Institute.}\\[0.5cm]

\begin{flushright}
\begin{table}[h]
\begin{tabular}{lr}
240301120081 & Ankit Singh \\ 
240301120089 & Naman Parashar \\
240301120094 & Priyanka Priyadarshini Nayak \\
240301120098 & Sonakshi Gupta \\
\end{tabular}
\end{table}
\end{flushright}

\begin{flushleft}
Place: Bhubaneswar\\
Date: 24th October 2026
\end{flushleft}

\vfill
\newpage
%\thispagestyle{empty}
\section*{} % unnumbered section not in ToC
\addcontentsline{toc}{section}{Acknowledgements}
\begin{center}
\underline{\LARGE \textbf{ACKNOWLEDGEMENTS}}\\[1.5cm]
\end{center}
\large{We wish to express our profound and sincere gratitude to Dr. Sunil Kumar Mohapatra, Department of Computer Science and Engineering, SoET, Bhubaneswar Campus, who guided us into the intricacies of this project nonchalantly with matchless magnanimity.\par
We thank Dr. Rahul Ray, Head of the Dept. of Department of Computer Science and Engineering, SoET, Bhubaneswar Campus and Dr. Swarna Prabha Jena, Associate Dean, School of Engineering and Technology, Bhubaneswar Campus for extending
their support during the course of this investigation. \par
We would be failing in our duty if we didn’t acknowledge the cooperation rendered during various stages of Project interpretation by
Dr. Sunil Kumar Mohapatra. \par
We are highly grateful to Dr. Sunil Kumar Mohapatra who evinced keen interest and invaluable
support in the progress and successful completion of our project work. \par
We are indebted to Dr. Sunil Kumar Mohapatra for his constant encouragement, cooperation, and help. Words of gratitude are not enough to describe the accommodation and fortitude that he has shown throughout our endeavor.}\\[0.5cm]
\begin{flushright}
\begin{table}[h]
\begin{tabular}{lr}
240301120081 & Ankit Singh \\ 
240301120089 & Naman Parashar \\
240301120094 & Priyanka Priyadarshini Nayak \\
240301120098 & Sonakshi Gupta \\
\end{tabular}
\end{table}
\end{flushright}

\begin{flushleft}
Place: Bhubaneswar\\
Date: 24th October 2026
\end{flushleft}

\newpage
%\thispagestyle{empty}
\section*{} % unnumbered section not in ToC
\addcontentsline{toc}{section}{Abstract}
\begin{center}
\underline{\LARGE \textbf{ABSTRACT}}\\[1.5cm]
\end{center}
\vspace{0.5cm}

\noindent Autonomous driving and Advanced Driver Assistance Systems (ADAS) depend critically on reliable visual perception to safely navigate complex road environments. However, real-world deployment faces severe performance degradation under adverse atmospheric and illumination conditions, such as nighttime darkness, heavy precipitation, and dense fog. Standard deep object detectors experience dramatic drops in detection confidence, erratic bounding box localization, and excessive false positive triggers when subjected to non-uniform illumination, specular reflections, and atmospheric light scattering. Furthermore, existing vision benchmarks like BDD100K suffer from extreme natural class imbalance, wherein critical adverse states such as dense fog account for less than 0.8\% of captured imagery. To resolve these challenges, this project presents \textbf{Adaptive Road Vision}, an end-to-end multi-stage deep learning perception and situational collision risk assessment framework. The proposed architecture integrates: (1) a multi-task ResNet-18 environmental condition classifier achieving 80.07\% accuracy across time-of-day and weather dimensions; (2) an unpaired CycleGAN domain adaptation module that overcomes natural data scarcity by synthesizing 3,000 realistic foggy road scenes subject to structural SSIM and veil-index quality screening; (3) condition-specific Residual U-Net restoration modules for low-light enhancement, rain streak suppression, and fog dehazing with a zero-latency direct bypass for clear daytime scenes; (4) fine-tuned YOLO11 detectors, wherein YOLO11s achieves 43.34\% mAP@50 and 22.21\% mAP@50-95 across 10 BDD100K road user classes; (5) Depth Anything V2 monocular depth estimation for dense relative proximity extraction; (6) ByteTrack multi-object tracking for robust spatial-temporal trajectory association; and (7) a multi-factor situational collision risk engine that dynamically fuses non-linear obstacle proximity, vulnerability class weights, environmental hazard multipliers, and track persistence into a 5-tier safety warning hierarchy. Extensive empirical evaluations across 3,000 test road scenes demonstrate that adaptive restoration increases detection precision from 64.58\% to 69.89\% and suppresses false positives by 44.6\% (reducing false alarms from 21,444 to 11,883). The entire system is operationalized via a production-grade Python library, headless CLI pipelines, and an interactive Streamlit ADAS HUD dashboard supporting live camera feeds, recorded video processing, and telemetry export.

\vspace{0.8cm}
\noindent\textbf{Keywords:}
\begin{IEEEkeywords}
Autonomous Vehicles, Advanced Driver Assistance Systems (ADAS), Adverse Weather Perception, Multi-Task Condition Classification, CycleGAN Domain Adaptation, Deep Image Restoration, YOLO11 Object Detection, ByteTrack Tracking, Monocular Relative Depth, Situational Collision Risk Engine.
\end{IEEEkeywords}

\newpage
\tableofcontents
\myemptypage
\listoffigures
\listoftables

\renewcommand{\thepage}{\arabic{page}}
\setcounter{page}{1}
\newpage

%==============================================================================
% SECTION 1: INTRODUCTION
%==============================================================================
\section{Introduction}
\label{sec:introduction}

\subsection{Background and Motivation}
Perception is the foundational layer upon which modern Advanced Driver Assistance Systems (ADAS) and Autonomous Vehicles (AV) make safety-critical motion planning, path tracking, and emergency braking decisions. Monocular camera vision serves as the primary visual sensing modality in road perception due to its high spatial resolution, rich chromatic representation of traffic signage and signals, and low production hardware cost relative to LiDAR and radar arrays.

However, modern computer vision algorithms—predominantly convolutional neural networks (CNNs) and vision transformers (ViTs)—are implicitly biased toward nominal daylight operating conditions. When deployed in unconstrained real-world automotive environments, visual cameras suffer severe signal degradation caused by atmospheric phenomena and extreme illumination variations:
\begin{enumerate}[label=(\alph*)]
    \item \textbf{Nighttime and Low-Light Degradation:} Insufficient photon arrival yields low dynamic range, severe sensor shot noise, underexposed pedestrian silhouettes, and extreme local overexposure from oncoming headlight glare.
    \item \textbf{Precipitation and Rain Streaks:} Falling raindrops induce dynamic vertical streak occlusions, while standing road water creates specular reflections and light scattering that distort lane markings and mirror preceding vehicle brake lights.
    \item \textbf{Fog and Atmospheric Scattering:} Suspended water aerosols scatter reflected scene photons according to Koschmieder's Law, creating a bright atmospheric veil that attenuates contrast exponentially with depth, completely washing out distant road hazards.
\end{enumerate}

When standard object detectors (such as standard YOLO or Faster R-CNN) operate directly on degraded input frames, downstream feature activations in deep backbones become corrupted. Consequently, detectors exhibit missed detections of vulnerable road users, spurious false alarms on ground reflections, and jittering bounding box coordinates.

\subsection{Problem Statement}
Automotive perception under adverse weather presents three interconnected technical challenges:
\begin{enumerate}
    \item \textbf{Catastrophic Data Scarcity in Natural Benchmarks:} Large-scale driving datasets, such as the Berkeley DeepDrive (BDD100K) dataset \cite{yu2020bdd100k}, exhibit an overwhelming natural bias toward clear daytime driving. Real-world foggy conditions constitute less than 0.8\% of total collected data, rendering standard supervised training severely under-constrained and prone to severe overfitting for foggy conditions.
    \item \textbf{The Enhancement-Detection Dilemma:} Naive full-image denoising or aggressive non-adaptive enhancement filters frequently introduce blurring artifacts, color distortion, and computational latency that degrade, rather than improve, downstream detection performance \cite{gupta2024robust}. A perception architecture must adaptively condition its restoration operations on the precise atmospheric state of the scene.
    \item \textbf{Absence of Integrated Spatial-Temporal Risk Reasoning:} Typical vision systems stop at 2D bounding box detection. Without tracking continuity, monocular proximity estimation, and environmental hazard weighting, raw bounding boxes cannot communicate actionable collision threats to human drivers or automated emergency braking controllers.
\end{enumerate}

\subsection{Research Objectives}
To resolve these limitations, this project designs, implements, trains, and validates \textbf{Adaptive Road Vision}, a modular, deep learning multi-stage perception framework. The specific objectives achieved in this research are:
\begin{itemize}
    \item \textbf{Multi-Task Scene Understanding:} Construct an automated ResNet-18 classifier that simultaneously predicts the scene illumination (Day vs. Night) and atmospheric state (Clear vs. Rain vs. Fog) to generate dynamic routing signals.
    \item \textbf{Adversarial Domain Adaptation:} Implement an unpaired CycleGAN generative framework to synthesize photorealistic foggy road images, balancing the BDD100K dataset while enforcing structural integrity via SSIM and atmospheric veil-index constraints.
    \item \textbf{Condition-Specific Neural Restoration:} Design lightweight Residual U-Net architectures specifically parameterized for low-light illumination expansion, rain streak/reflection attenuation, and fog dehazing, featuring an intelligent zero-distortion bypass for clear daytime frames.
    \item \textbf{State-of-the-Art Object Detection:} Fine-tune Ultralytics YOLO11 architectures (YOLO11n and YOLO11s) across a curated 10-class automotive taxonomy under equalized adverse weather splits.
    \item \textbf{Unified Spatial-Temporal Tracking and Monocular Depth:} Couple YOLO detections with ByteTrack Kalman-based association and Depth Anything V2 foundation model depth inference to provide persistent track identities and ground-plane obstacle proximities.
    \item \textbf{Multi-Factor Situational Risk Engine:} Formulate a mathematically grounded risk engine that synthesizes obstacle proximity, pedestrian/cyclist vulnerability weights, scene weather multipliers, and track lifespan into an operational 5-tier safety hierarchy (SAFE, LOW, MEDIUM, HIGH, CRITICAL).
    \item \textbf{End-to-End ADAS Telemetry and Dashboard:} Operationalize the complete pipeline into a high-speed OpenCV HUD renderer ($<3\text{ ms}$ overlay latency) and an interactive Streamlit web dashboard capable of batch image processing, recorded video inference, and live webcam telemetry.
\end{itemize}

\subsection{Organization of the Report}
The remainder of this report is organized as follows: Section~\ref{sec:literature_review} presents a comprehensive review of related literature across image restoration, adverse weather driving, object detection, tracking, and monocular depth, including a structured comparative table of 15 seminal papers. Section~\ref{sec:methodology} elaborates on the system architecture, mathematical formulations, and algorithms governing each stage. Section~\ref{sec:dataset} details the BDD100K dataset engineering, CycleGAN domain synthesis, and balanced split preparation. Section~\ref{sec:implementation} outlines the training protocols, hardware configuration, and software design. Section~\ref{sec:results} presents quantitative empirical results, component ablation studies, and discussion. Section~\ref{sec:challenges} analyzes system limitations and failure modes. Finally, Section~\ref{sec:conclusion} concludes the project and outlines prospective future research directions.

\newpage
%==============================================================================
% SECTION 2: LITERATURE REVIEW
%==============================================================================
\section{Literature Review and Related Work}
\label{sec:literature_review}

\subsection{Theoretical Foundations of Road Perception Under Adverse Conditions}
Road perception under adverse weather intersects multiple computer vision disciplines: low-light enhancement, deraining, single-image dehazing, domain adaptation, multi-object tracking, and monocular depth estimation.

In low-light enhancement, classical histogram equalization and Retinex decomposition \cite{xu2020decomposition} have evolved toward deep curve estimation models like Zero-DCE \cite{guo2020zero} and Zero-DCE++ \cite{li2021zero}, which learn non-linear pixel-wise adjustment curves without paired ground truth. More recently, Retinexformer \cite{cai2023retinexformer} demonstrated the power of transformer-based illumination-guided restoration, although its heavy computational budget presents challenges for edge automotive deployment.

In weather restoration, rain streaks and droplets pose severe visibility challenges. Quan et al. \cite{quan2021ccn} introduced complementary cascaded networks (CCN) to jointly eliminate raindrops and rain streaks. For haze and fog, contrastive regularization in AECR-Net \cite{wu2021aecrnet} and self-attention in DehazeFormer \cite{song2023dehazeformer} provide powerful single-image dehazing by inverting Koschmieder's scattering model. Generic architectures like AirNet \cite{li2022airnet} and Restormer \cite{zamir2022restormer} attempt all-in-one restoration across unknown degradations, but require substantial GPU compute.

For downstream road perception, Gupta et al. \cite{gupta2024robust} established a pivotal benchmark showing that blindly prepending general-purpose denoising models to object detectors often harms detection accuracy due to high-frequency feature suppression. Instead, detectors trained on diverse real-weather datasets (e.g., BDD100K \cite{yu2020bdd100k} and ACDC \cite{sakaridis2021acdc}) achieve superior robustness. Lightweight specialized detectors, such as MLE-YOLO \cite{du2026mleyolo}, emphasize multi-scale adverse weather feature extraction.

In tracking and spatial depth, ByteTrack \cite{zhang2022bytetrack} revolutionized multi-object tracking by associating low-confidence bounding boxes rather than discarding them, recovering occluded vehicles and pedestrians. Concurrently, foundation models such as Depth Anything \cite{yang2024depth} established zero-shot monocular relative depth estimation across diverse driving topographies.

\subsection{Systematic Literature Survey (Table 1)}
To contextualize the proposed Adaptive Road Vision framework within the state-of-the-art, Table~\ref{tab:related_work} synthesizes 15 seminal research works covering low-light enhancement, deraining, dehazing, driving benchmarks, lightweight detection, tracking, and depth estimation.

\afterpage{
\clearpage
\begin{landscape}
\centering
\small
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.15}
\begin{longtable}{p{0.5cm} p{2.4cm} p{0.8cm} p{3.2cm} p{3.2cm} p{3.5cm} p{3.0cm} p{3.2cm} p{1.6cm}}
\caption{Related Work for Adaptive Road Vision Enhancement and Risk-Aware Object Detection} \label{tab:related_work} \\
\toprule
\textbf{No.} & \textbf{Authors} & \textbf{Year} & \textbf{Methodology Used} & \textbf{Dataset Used} & \textbf{Findings} & \textbf{Accuracy / Performance} & \textbf{Limitations} & \textbf{Links} \\
\midrule
\endfirsthead
\multicolumn{9}{c}%
{{\bfseries Table \thetable\ continued from previous page}} \\
\toprule
\textbf{No.} & \textbf{Authors} & \textbf{Year} & \textbf{Methodology Used} & \textbf{Dataset Used} & \textbf{Findings} & \textbf{Accuracy / Performance} & \textbf{Limitations} & \textbf{Links} \\
\midrule
\endhead
\midrule
\multicolumn{9}{r}{{Continued on next page}} \\
\bottomrule
\endfoot
\bottomrule
\endlastfoot

1 & Fisher Yu, Haofeng Chen, Xin Wang, et al. \cite{yu2020bdd100k} & 2020 & \textbf{BDD100K} --- diverse driving-video dataset supporting detection, tracking, segmentation and multiple environmental conditions & \textbf{BDD100K} --- 100K driving videos; road-object detection, tracking, weather/environment diversity & Provides a large-scale and diverse benchmark for real-world road perception and supports multiple autonomous-driving tasks. & Multiple benchmark metrics; detection and tracking benchmarks provided rather than one overall accuracy. & Weather/condition distribution is not perfectly balanced; rare adverse conditions (fog $<0.8\%$) can be severely underrepresented. & \href{https://bdd-data.berkeley.edu/}{Dataset} \href{https://arxiv.org/abs/1704.07340}{Paper} \\
\midrule

2 & Chunle Guo, Chongyi Li, Jichang Guo, et al. \cite{guo2020zero} & 2020 & \textbf{Zero-DCE} --- zero-reference deep curve estimation for low-light enhancement & SICE, LIME, MEF, DICM, VV, DARK FACE and other low-light benchmarks & Learns image-specific enhancement curves without requiring paired low/normal-light images; lightweight and useful for dark-scene enhancement. & Reported improvements using PSNR/SSIM and other enhancement metrics; also evaluated on dark face detection. & Designed primarily for low-light conditions; does not specifically solve precipitation, water reflections, or fog. & \href{https://github.com/Li-Chongyi/Zero-DCE}{Project} \href{https://openaccess.thecvf.com/content_CVPR_2020/papers/Guo_Zero-Reference_Deep_Curve_Estimation_for_Low-Light_Image_Enhancement_CVPR_2020_paper.pdf}{Paper} \\
\midrule

3 & Ke Xu, Xin Yang, Baocai Yin, Rynson W.H. Lau \cite{xu2020decomposition} & 2020 & \textbf{Decomposition-and-Enhancement} --- frequency-based low-light restoration with noise handling & Real noisy low-light dataset introduced by authors; additional low-light benchmarks & Recovers low-frequency image structure and enhances high-frequency details, specifically addressing sensor noise in low light. & Outperformed compared state-of-the-art methods on practical noisy low-light image enhancement benchmarks. & More computationally involved; focused purely on low-light rather than multi-weather atmospheric conditions. & \href{https://openaccess.thecvf.com/content_CVPR_2020/papers/Xu_Learning_to_Restore_Low-Light_Images_via_Decomposition-and-Enhancement_CVPR_2020_paper.pdf}{Paper} \\
\midrule

4 & Christos Sakaridis, Dengxin Dai, Luc Van Gool \cite{sakaridis2021acdc} & 2021 & \textbf{ACDC} --- adverse-condition driving dataset with normal/adverse scene correspondences & \textbf{ACDC} --- 4,006 images: fog, nighttime, rain and snow, approximately equally distributed & Provides realistic adverse-condition road scenes and corresponding normal-condition images for robust driving perception. & Benchmark supports semantic-segmentation metrics; not a single classification accuracy. & Mainly designed for semantic segmentation; does not directly provide the complete detection $\to$ tracking $\to$ distance $\to$ risk pipeline. & \href{https://acdc.vision.ee.ethz.ch/}{Dataset} \href{https://openaccess.thecvf.com/content/ICCV2021/papers/Sakaridis_ACDC_The_Adverse_Conditions_Dataset_With_Correspondences_for_Semantic_ICCV_2021_paper.pdf}{Paper} \\
\midrule

5 & Ruijie Quan, Xin Yu, Yuanzhi Liang, Yi Yang \cite{quan2021ccn} & 2021 & \textbf{CCN} --- complementary cascaded network for removing raindrops and rain streaks & \textbf{RainDS} + existing deraining benchmarks (rain-streak, raindrop and combined-rain images) & Jointly removes raindrops and rain streaks rather than treating them as separate degradation problems. & Reported state-of-the-art performance on existing benchmarks and RainDS using image-restoration metrics. & Focuses on rain removal; does not jointly handle night/fog and downstream object collision risk assessment. & \href{https://openaccess.thecvf.com/content/CVPR2021/papers/Quan_Removing_Raindrops_and_Rain_Streaks_in_One_Go_CVPR_2021_paper.pdf}{Paper} \\
\midrule

6 & Haiyan Wu, Yanyun Qu, Shaohui Lin, et al. \cite{wu2021aecrnet} & 2021 & \textbf{AECR-Net} --- compact dehazing network using contrastive regularization & Synthetic and real-world dehazing datasets including \textbf{RESIDE} & Uses clear images as positive information and hazy images as negative information while maintaining a compact architecture. & Reported improved PSNR/SSIM and competitive state-of-the-art dehazing performance. & Designed specifically for single image dehazing; not an integrated road-video perception system. & \href{https://openaccess.thecvf.com/content/CVPR2021/papers/Wu_Contrastive_Learning_for_Compact_Single_Image_Dehazing_CVPR_2021_paper.pdf}{Paper} \\
\midrule

7 & Chongyi Li, Chunle Guo, Chen Change Loy \cite{li2021zero} & 2021 & \textbf{Zero-DCE++} --- accelerated lightweight version of Zero-DCE for low-light enhancement & SICE and other low-light benchmarks & Uses a very small network and provides significantly faster inference while retaining enhancement capability of Zero-DCE. & About 1000 FPS on GPU / 11 FPS on CPU reported for $1200\times 900$ images; $\sim$10K parameters. & Primarily designed for low-light enhancement, not rain/fog; reported speed depends heavily on hardware and resolution. & \href{https://github.com/Li-Chongyi/Zero-DCE_extension}{Project} \href{https://arxiv.org/abs/2102.00800}{Paper} \\
\midrule

8 & Boyun Li, Xiao Liu, Peng Hu, et al. \cite{li2022airnet} & 2022 & \textbf{AirNet} --- All-in-One Image Restoration Network for unknown corruption types & Four challenging image-restoration datasets covering different corruptions & A single network can restore different unknown degradation types without explicitly knowing corruption type or level. & Outperformed 17 image-restoration baselines across four challenging datasets. & Generic restoration may not be optimal for specific road-weather physics; computational cost is high for edge deployment. & \href{https://github.com/XLearning-SCU/2022-CVPR-AirNet}{Code} \href{https://openaccess.thecvf.com/content/CVPR2022/papers/Li_All-in-One_Image_Restoration_for_Unknown_Corruption_CVPR_2022_paper.pdf}{Paper} \\
\midrule

9 & Yifu Zhang, Peize Sun, Yi Jiang, et al. \cite{zhang2022bytetrack} & 2022 & \textbf{ByteTrack} --- associates almost every detection box to improve multi-object tracking & MOT17, MOT20, HiEve and \textbf{BDD100K tracking} & Improves tracking by associating low-confidence detections instead of discarding them, recovering occluded objects and reducing fragmented tracks. & 80.3 MOTA, 77.3 IDF1, 63.1 HOTA at 30 FPS on MOT17 using a V100 GPU. & Tracking quality depends heavily on upstream detector; severe rain/fog/night can still cause total missed detections. & \href{https://github.com/ifzhang/ByteTrack}{Code} \href{https://arxiv.org/abs/2110.06864}{Paper} \\
\midrule

10 & Syed Waqas Zamir, Aditya Arora, Salman Khan, et al. \cite{zamir2022restormer} & 2022 & \textbf{Restormer} --- efficient Transformer for high-resolution image restoration (deraining, denoising) & Multiple image-restoration benchmarks, including deraining and denoising datasets & Efficient Transformer architecture achieves strong restoration performance while handling long-range pixel interactions. & State-of-the-art/competitive results across several restoration benchmarks. & Transformer-based restoration is computationally heavy, rendering edge/real-time vehicle deployment difficult. & \href{https://github.com/swz30/Restormer}{Code} \href{https://openaccess.thecvf.com/content/CVPR2022/papers/Zamir_Restormer_Efficient_Transformer_for_High-Resolution_Image_Restoration_CVPR_2022_paper.pdf}{Paper} \\
\midrule

11 & Yuanhao Cai, Hao Bian, Jing Lin, et al. \cite{cai2023retinexformer} & 2023 & \textbf{Retinexformer} --- one-stage Retinex-based Transformer for low-light enhancement & 13 low-light benchmarks & Uses illumination estimation followed by restoration and illumination-guided Transformer; evaluates value for low-light detection. & Reported strong state-of-the-art results across 13 benchmarks; low-light object detection application also evaluated. & Substantially more complex than lightweight curve-based models, hindering real-time edge vehicle deployment. & \href{https://openaccess.thecvf.com/content/ICCV2023/papers/Cai_Retinexformer_One-stage_Retinex-based_Transformer_for_Low-light_Image_Enhancement_ICCV_2023_paper.pdf}{Paper} \\
\midrule

12 & Yuda Song, Zhuqing He, Hui Qian, Xin Du \cite{song2023dehazeformer} & 2023 & \textbf{DehazeFormer} --- Vision Transformer architecture for single-image dehazing & SOTS and additional synthetic/real-world dehazing datasets & Uses Transformer-based feature representation to improve single-image dehazing, effectively clearing realistic haze. & Strong dehazing performance with competitive PSNR/SSIM compared with existing methods. & Focuses on fog/haze only; not designed for combined night + fog/rain road perception pipelines. & \href{https://openaccess.thecvf.com/content/CVPR2023/papers/Song_Vision_Transformers_for_Single_Image_Dehazing_CVPR_2023_paper.pdf}{Paper} \\
\midrule

13 & Himanshu Gupta, Oleksandr Kotlyar, Henrik Andreasson, Achim J. Lilienthal \cite{gupta2024robust} & 2024 & \textbf{Robust Object Detection in Challenging Weather} --- compares real-weather training, synthetic augmentation and denoising & \textbf{BDD100K} + unseen real-world adverse-weather images & Found that training with real all-weather images performed best, while simply detecting on denoised images performed worst among evaluated strategies. & Evaluated object-detection performance under adverse weather; results support using real adverse-weather training data. & Shows enhancement alone does not guarantee detection gains; does not provide an integrated tracking + distance + risk system. & \href{https://arxiv.org/abs/2402.16688}{Paper} \\
\midrule

14 & Lihe Yang, Bingyi Kang, Zilong Huang, et al. \cite{yang2024depth} & 2024 & \textbf{Depth Anything} --- large-scale monocular depth-estimation foundation model & 1.5M labeled + 62M+ unlabeled images; evaluated on KITTI, NYUv2, etc. & Provides robust monocular depth estimation and strong zero-shot generalization across diverse driving scenes and conditions. & Strong zero-shot performance; fine-tuning on KITTI/NYUv2 achieved new state-of-the-art results. & Foundation model parameters can be heavy for lightweight real-time deployment; monocular depth naturally lacks metric scale without calibration. & \href{https://depth-anything.github.io/}{Project} \href{https://arxiv.org/abs/2401.10891}{Paper} \\
\midrule

15 & Danfeng Du, Mengju Bi, Yuchen Xie, et al. \cite{du2026mleyolo} & 2026 & \textbf{MLE-YOLO} --- lightweight and robust YOLO-based detector for vehicle/pedestrian detection under adverse weather & \textbf{AWPD}; also discusses DAWN and BDD100K benchmarks & Designed specifically for adverse-weather vehicle and pedestrian detection while reducing computational requirements. & Reports +3.6\% F1, +3.0\% mAP, $-$15.8\% parameters, $-$7.1\% model size, $-$3.2\% FLOPs compared with baseline. & Focuses strictly on bounding box detection; lacks upstream adaptive image enhancement and downstream tracking/risk reasoning. & \href{https://arxiv.org/abs/2601.08900}{Paper} \\
\bottomrule
\end{longtable}
\end{landscape}
\clearpage
}

\subsection{Research Gaps and Project Novelty}
As synthesized in Table~\ref{tab:related_work}, existing literature is divided into isolated sub-problems:
\begin{enumerate}
    \item \textbf{Decoupled Image Restoration vs. Object Detection:} Studies either design heavy restoration networks (e.g., Restormer \cite{zamir2022restormer}, Retinexformer \cite{cai2023retinexformer}) that optimize purely for pixel fidelity (PSNR/SSIM) without considering downstream detection latency, or design detectors that struggle when severe atmospheric veil obscures features.
    \item \textbf{Unaddressed Real-World Fog Scarcity:} While datasets like BDD100K \cite{yu2020bdd100k} provide massive scale, real-world foggy road samples represent $<0.8\%$ of data. A principled generative domain-adaptation strategy that augments real road geometry with realistic fog while passing strict structural verification has been missing.
    \item \textbf{Lack of Integrated Spatial-Temporal Risk Reasoning:} No prior work integrates condition classification, domain adaptation, condition-specific neural enhancement, high-speed detection, ByteTrack tracking \cite{zhang2022bytetrack}, monocular depth estimation \cite{yang2024depth}, and multi-factor situational risk scoring into a unified, real-time ADAS pipeline.

    Adaptive Road Vision directly bridges these critical gaps.
\end{enumerate}

\newpage
%==============================================================================
% SECTION 3: SYSTEM ARCHITECTURE AND METHODOLOGY
%==============================================================================
\section{System Architecture and Theoretical Formulation}
\label{sec:methodology}

\subsection{Architectural Overview}
The Adaptive Road Vision framework is structured as an end-to-end, multi-stage perceptual pipeline. Figure~\ref{fig:pipeline_flowchart} illustrates the logical flow: an incoming raw camera frame is classified for illumination and weather state, routed to an appropriate neural enhancer, processed by a fine-tuned YOLO11 detector and Depth Anything V2 depth estimator, tracked across temporal frames via ByteTrack, and assessed by a multi-factor collision risk engine.

\begin{figure}[!ht]
\centering
\fbox{\parbox{0.92\textwidth}{
\centering
\vspace{0.3cm}
\textbf{\large Complete Multi-Stage Perceptual Flowchart}\\[0.3cm]
\small
$\text{Raw Camera Frame } I \in \mathbb{R}^{H \times W \times 3}$
\\[0.15cm]
$\Downarrow$
\\[0.15cm]
\textbf{[Stage 1: Multi-Task Condition Classifier (ResNet-18)]}\\
$\text{Predicts: Time } (\text{Day}/\text{Night}) \quad \& \quad \text{Weather } (\text{Clear}/\text{Rain}/\text{Fog})$
\\[0.15cm]
$\Downarrow$
\\[0.15cm]
\textbf{[Stage 2: Adaptive Neural Restoration Router]}\\
$\text{Night} \to \text{Low-Light U-Net} \quad \mid \quad \text{Rain} \to \text{Deraining U-Net} \quad \mid \quad \text{Fog} \to \text{Dehazing U-Net} \quad \mid \quad \text{Day+Clear} \to \text{Pass-Through}$
\\[0.15cm]
$\Downarrow$
\\[0.15cm]
$\text{Enhanced Frame } \hat{I} \in \mathbb{R}^{H \times W \times 3}$
\\[0.15cm]
$\swarrow \quad \searrow$
\\[0.15cm]
\textbf{[Stage 3: Object Detection (YOLO11s)]} \qquad \qquad \textbf{[Stage 4: Relative Depth (Depth Anything V2)]}\\
$\text{Boxes, Confidences, 10 BDD Classes}$ \qquad \qquad $\text{Dense Proximity Map } D(u, v) \in [0, 1]$
\\[0.15cm]
$\searrow \quad \swarrow$
\\[0.15cm]
\textbf{[Stage 5: Multi-Object Tracking (ByteTrack)]}\\
$\text{Temporal Kalman Association, Persistent Track IDs, Trajectory History}$
\\[0.15cm]
$\Downarrow$
\\[0.15cm]
\textbf{[Stage 6: Multi-Factor Situational Collision Risk Engine]}\\
$\text{Risk}_i = (\text{Prox}_i)^{1.3} \cdot W_{\text{class}} \cdot M_{\text{cond}} \cdot \text{Conf}_i \cdot P_{\text{age}}$
\\[0.15cm]
$\Downarrow$
\\[0.15cm]
\textbf{[Stage 7: ADAS HUD Visualization \& Telemetry Warning]}\\
$\text{Dynamic Bounding Boxes, Proximity Gauges, Auditory/Visual Collision Alerts}$
\vspace{0.3cm}
}}
\caption{End-to-end architectural flowchart of the Adaptive Road Vision perception pipeline.}
\label{fig:pipeline_flowchart}
\end{figure}

\subsection{Stage 1: Multi-Task Environmental Condition Classifier}
The initial perceptual task is to determine the atmospheric and temporal state of the scene without manual user intervention. Instead of training two separate networks, we design a unified multi-task deep neural network based on a convolutional ResNet-18 backbone.

Given an input image $I \in \mathbb{R}^{224 \times 224 \times 3}$, the backbone extracts a 512-dimensional feature embedding $\mathbf{f} = \text{GAP}(\text{ResNet18}(I))$. The feature vector is passed through a dropout layer ($p=0.2$) into two parallel fully connected classification heads:
\begin{enumerate}
    \item \textbf{Time-of-Day Head:} Computes logits $\mathbf{z}_{\text{time}} \in \mathbb{R}^2$ corresponding to $\{\text{Day}, \text{Night}\}$.
    \item \textbf{Weather Condition Head:} Computes logits $\mathbf{z}_{\text{weather}} \in \mathbb{R}^3$ corresponding to $\{\text{Clear}, \text{Rain}, \text{Fog}\}$.
\end{enumerate}

The joint multi-task loss function during supervised training is formulated as:
\begin{equation}
\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{time}}(\mathbf{z}_{\text{time}}, y_{\text{time}}) + \lambda_{\text{weather}} \mathcal{L}_{\text{weather}}(\mathbf{z}_{\text{weather}}, y_{\text{weather}})
\label{eq:condition_loss}
\end{equation}
where $\mathcal{L}_{\text{time}}$ and $\mathcal{L}_{\text{weather}}$ represent cross-entropy losses, and $\lambda_{\text{weather}} = 1.20$ is an empirically tuned weight balancing the gradient contributions of the 3-class weather head against the binary time head.

During inference, class probabilities are computed via softmax:
\begin{equation}
p_{\text{time}} = \text{softmax}(\mathbf{z}_{\text{time}}), \quad p_{\text{weather}} = \text{softmax}(\mathbf{z}_{\text{weather}})
\end{equation}
The dominant condition routing signal $k \in \{\text{Day}, \text{Night}, \text{Rain}, \text{Fog}\}$ is assigned hierarchically: if $\arg\max(p_{\text{weather}}) = \text{Fog}$, the scene is routed to Fog; else if $\arg\max(p_{\text{weather}}) = \text{Rain}$, it is routed to Rain; else if $\arg\max(p_{\text{time}}) = \text{Night}$, it is routed to Night; otherwise, the scene is designated Day (Clear).

\subsection{Stage 2: CycleGAN Domain Adaptation for Fog Scarcity Mitigation}
In the natural BDD100K driving dataset, genuine fog images represent fewer than $0.8\%$ of total frames (under 600 total instances). Direct training under this severe class scarcity results in poor generalization and high false alarm rates. To resolve this, we employ an unpaired Cycle-Consistent Generative Adversarial Network (CycleGAN) to perform offline domain adaptation from clear day/night driving scenes to foggy environments.

Following Koschmieder's physical scattering model:
\begin{equation}
I(x) = J(x) t(x) + A (1 - t(x))
\label{eq:koschmieder}
\end{equation}
where $I(x)$ is the observed foggy intensity at pixel $x$, $J(x)$ is original scene radiance, $t(x) = e^{-\beta d(x)}$ is the atmospheric transmission along distance $d(x)$ with attenuation coefficient $\beta$, and $A$ is the atmospheric light.

The CycleGAN system consists of two generators and two discriminators:
\begin{itemize}
    \item $G_{AB}: X_{\text{clear}} \to Y_{\text{fog}}$ (synthesizes foggy veil over clear road geometry).
    \item $G_{BA}: Y_{\text{fog}} \to X_{\text{clear}}$ (reconstructs clear road scenes from foggy inputs).
    \item $D_A, D_B$: $70 \times 70$ PatchGAN discriminators classifying local image patches as authentic or generated.
\end{itemize}

The training objective optimizes a compound loss function:
\begin{equation}
\mathcal{L}(G_{AB}, G_{BA}, D_A, D_B) = \mathcal{L}_{\text{GAN}}(G_{AB}, D_B) + \mathcal{L}_{\text{GAN}}(G_{BA}, D_A) + \lambda_{\text{cyc}} \mathcal{L}_{\text{cyc}} + \lambda_{\text{idt}} \mathcal{L}_{\text{idt}}
\label{eq:cyclegan_loss}
\end{equation}
where cycle consistency loss enforces structural conservation:
\begin{equation}
\mathcal{L}_{\text{cyc}} = \mathbb{E}_{x \sim X}[\| G_{BA}(G_{AB}(x)) - x \|_1] + \mathbb{E}_{y \sim Y}[\| G_{AB}(G_{BA}(y)) - y \|_1]
\end{equation}
with $\lambda_{\text{cyc}} = 10.0$ and identity regularization $\lambda_{\text{idt}} = 5.0$.

To guarantee that synthetic fog images do not introduce hallucinated road obstacles or structural distortions, an automated quality screening gate is enforced:
\begin{equation}
\text{Acceptance Condition} = \left(\text{SSIM}(x, G_{AB}(x)) \ge 0.72\right) \land \left(\Delta \text{Veil} \ge \tau_{\text{fog}}\right)
\end{equation}
Across 3,000 synthesized images (1,500 Day$\to$Fog, 1,500 Night$\to$Fog), 2,802 images ($93.4\%$) satisfied strict quality standards and were integrated into the primary training dataset (`final_condition_balanced_v2`).

\subsection{Stage 3: Adaptive Neural Restoration Router and Condition U-Nets}
Rather than applying a computationally expensive, monolithic restoration network across every video frame, Adaptive Road Vision incorporates an \textbf{Adaptive Router} that directs input frames to lightweight condition-specific Residual U-Nets:
\begin{enumerate}
    \item \textbf{Night Enhancer:} Restores underexposed dark road regions, expands dynamic range, suppresses sensor noise, and regulates headlight glare. Target pseudo-ground-truth is generated via non-linear gamma correction ($\gamma = 0.78$) and adaptive contrast enhancement:
    \begin{equation}
    I_{\text{target, night}} = \text{clip}\left( (\alpha \cdot I_{\text{bright}})^{\gamma}, 0, 1 \right)
    \end{equation}
    \item \textbf{Rain Enhancer:} Attenuates high-frequency specular road reflections, wiper streaks, and water glare. Target targets are derived from structural median filtering blended with original high-frequency edge gradients:
    \begin{equation}
    I_{\text{target, rain}} = 0.70 \cdot \text{MedianFilter}(I, 3 \times 3) + 0.30 \cdot I
    \end{equation}
    \item \textbf{Fog Enhancer:} Inverts the atmospheric veil by estimating low-frequency veil components and recovering localized dark-channel contrast:
    \begin{equation}
    I_{\text{target, fog}} = \text{clip}\left( \frac{I - 0.35 \cdot \text{GaussianFilter}(I, \sigma=4.0)}{1.0 - 0.35 + \epsilon} \cdot 1.15, 0, 1 \right)
    \end{equation}
    \item \textbf{Day + Clear Bypass:} Under clear daytime conditions, the router bypasses enhancement entirely ($0\text{ ms}$ processing overhead, $0.0\%$ distortion), preserving original sensor fidelity.
\end{enumerate}

Each restoration U-Net features 3 encoder stages (channel depths 32, 64, 128), a bottleneck of 4 residual blocks with instance normalization and ReLU activation, and 2 decoder stages with bilinear upsampling and skip-connections. The output layer predicts a bounded residual:
\begin{equation}
\hat{I} = \text{clip}\left( I + 0.5 \cdot \tanh(\text{Conv}_{3\times 3}(\mathbf{z}_{\text{dec}})), 0.0, 1.0 \right)
\label{eq:residual_unet}
\end{equation}
The residual formulation guarantees numerical stability and prevents catastrophic semantic drift during real-time execution.

\subsection{Stage 4: YOLO11 Object Detection Architecture}
Object detection is performed using the Ultralytics YOLO11 architecture, fine-tuned across the 10 BDD100K road user categories: \texttt{person}, \texttt{rider}, \texttt{car}, \texttt{truck}, \texttt{bus}, \texttt{train}, \texttt{motorcycle}, \texttt{bicycle}, \texttt{traffic light}, and \texttt{traffic sign}.

YOLO11 introduces substantial architectural enhancements over earlier YOLO generations:
\begin{itemize}
    \item \textbf{C3k2 Backbone Blocks:} Employs cross-stage partial connections with depthwise separable convolutions to expand receptive field capacity while reducing FLOPs.
    \item \textbf{SPPF (Spatial Pyramid Pooling - Fast):} Concatenates multi-scale max-pooling features ($5\times 5$, $9\times 9$, $13\times 13$) to capture long-range contextual cues essential for detecting distant road users in low-visibility scenes.
    \item \textbf{Decoupled Anchor-Free Head:} Separates bounding box regression (DFL: Distribution Focal Loss + Complete IoU) from classification (Binary Cross-Entropy with Task-Aligned Assigner):
    \begin{equation}
    \mathcal{L}_{\text{det}} = \lambda_{\text{box}} \mathcal{L}_{\text{CIoU}} + \lambda_{\text{dfl}} \mathcal{L}_{\text{DFL}} + \lambda_{\text{cls}} \mathcal{L}_{\text{BCE}}
    \end{equation}
\end{itemize}

Two candidate detectors were trained and benchmarked under identical conditions: **Detector 1 (YOLO11n)** (ultralight baseline, 2.6M parameters) and **Detector 2 (YOLO11s)** (compact high-accuracy model, 9.4M parameters). Non-Maximum Suppression (NMS) is applied with confidence threshold $\tau_{\text{conf}} = 0.25$ and IoU threshold $\tau_{\text{IoU}} = 0.50$.

\subsection{Stage 5: Monocular Relative Depth Estimation}
Autonomous situational awareness requires distance awareness. Rather than requiring expensive dual-camera stereo rigs or LiDAR sensors, Adaptive Road Vision incorporates the **Depth Anything V2 Small** foundation model \cite{yang2024depth}.

Given an RGB frame $I \in \mathbb{R}^{518 \times 518 \times 3}$, Depth Anything V2 outputs a continuous relative inverse depth map $D(u, v) \in [0.0, 1.0]$, where values near $1.0$ indicate immediate vehicle proximity and $0.0$ represents distant infinity.

For each detected object $i$ with bounding box $[x_1, y_1, x_2, y_2]$, obstacle proximity is extracted from the ground-contact region (the bottom 30\% of the bounding box):
\begin{equation}
\text{Prox}_i = \text{Quantile}_{0.30} \left( \{ D(u, v) \mid u \in [x_1, x_2], \, v \in [y_1 + 0.70(y_2 - y_1), y_2] \} \right)
\label{eq:depth_quantile}
\end{equation}
The 30th percentile quantile filter prevents background sky or road horizon leakage from distorting the true ground contact plane. When GPU depth estimation is disabled or resource-constrained, an analytical geometric perspective fallback is computed:
\begin{equation}
\text{Prox}_{\text{geo}} = \min\left( 1.0, \frac{y_2}{H} \cdot \frac{y_2 - y_1}{H} \cdot 2.2 \right)
\end{equation}
where $H$ is frame height and $y_2$ is the bottom box coordinate.

\subsection{Stage 6: ByteTrack Multi-Object Tracking}
Single-frame detections suffer from temporal flicker and intermittent occlusions under adverse weather. To establish temporal continuity, the pipeline integrates **ByteTrack** \cite{zhang2022bytetrack}.

ByteTrack maintains an 8-dimensional motion state vector for each tracked object via a linear Kalman filter:
\begin{equation}
\mathbf{x}_t = [x, y, a, h, \dot{x}, \dot{y}, \dot{a}, \dot{h}]^T
\end{equation}
where $(x, y)$ is the bounding box center, $a$ is aspect ratio, $h$ is box height, and the dotted terms represent instantaneous velocities.

ByteTrack executes a two-stage association strategy:
\begin{enumerate}
    \item \textbf{First Association:} High-confidence detections ($s_i \ge 0.50$) are matched against active Kalman tracks using the Hungarian algorithm based on bounding box IoU distance.
    \item \textbf{Second Association:} Unmatched active tracks are matched against low-confidence detections ($0.10 \le s_i < 0.50$). This step recovers occluded pedestrians or vehicles obscured by rain streaks or fog without propagating false background detections.
\end{enumerate}
Tracks are maintained across occlusions using a 30-frame temporal lifespan buffer.

\subsection{Stage 7: Multi-Factor Situational Collision Risk Engine}
To translate perception outputs into actionable driving safety commands, we design a transparent, deterministic collision risk engine. The situational risk score $\text{Risk}_i \in [0.0, 1.0]$ for each tracked obstacle $i$ is formulated as:
\begin{equation}
\text{Risk}_i = \min\left( 1.0, (\text{Prox}_i)^{1.3} \cdot W_{\text{class}}(c_i) \cdot M_{\text{cond}}(k) \cdot \max(0.25, s_i) \cdot P_{\text{age}}(t_i) \right)
\label{eq:risk_formula}
\end{equation}
where:
\begin{itemize}
    \item $(\text{Prox}_i)^{1.3}$ provides a non-linear proximity ramp that heavily penalizes obstacles entering the near-field safety buffer.
    \item $W_{\text{class}}(c_i)$ assigns vulnerability weighting according to road user physical mass and vulnerability (Table~\ref{tab:risk_weights}).
    \item $M_{\text{cond}}(k)$ represents atmospheric hazard multipliers reflecting extended vehicle braking distances on wet or low-visibility roads (Table~\ref{tab:risk_weights}).
    \item $\max(0.25, s_i)$ incorporates detection confidence, bounded by a confidence floor to prevent low-confidence noise spikes.
    \item $P_{\text{age}}(t_i) = \min(1.0, 0.70 + 0.30 \cdot \frac{t_i}{10})$ is a track persistence factor that stabilizes transient false detections while rapidly escalating confirmed persistent obstacles.
\end{itemize}

\begin{table}[!ht]
\centering
\caption{Taxonomy Weights and Atmospheric Hazard Multipliers}
\label{tab:risk_weights}
\begin{tabular}{lc|lc}
\toprule
\textbf{BDD100K Object Class} & \textbf{Vulnerability Weight ($W_{\text{class}}$)} & \textbf{Environmental Condition} & \textbf{Hazard Multiplier ($M_{\text{cond}}$)} \\
\midrule
Person (Pedestrian) & 1.30 & Day + Clear & 1.00$\times$ \\
Rider (Cyclist/Scooter) & 1.25 & Unknown / Overcast & 1.05$\times$ \\
Motorcycle & 1.20 & Rain (Wet Road Surface) & 1.15$\times$ \\
Bicycle & 1.20 & Night (Low Ambient Light) & 1.20$\times$ \\
Truck & 1.05 & Fog (Dense Veil) & 1.25$\times$ \\
Bus & 1.05 & & \\
Car & 1.00 & & \\
Train & 1.00 & & \\
Traffic Light & 0.80 & & \\
Traffic Sign & 0.80 & & \\
\bottomrule
\end{tabular}
\end{table}

The aggregate scene collision risk for an entire video frame is computed by combining the peak obstacle risk with contextual contributions from secondary obstacles:
\begin{equation}
\text{Risk}_{\text{frame}} = \min\left( 1.0, \max_i(\text{Risk}_i) + 0.15 \sum_{j \neq i^*} \text{Risk}_j \right)
\label{eq:frame_risk}
\end{equation}
Frames are classified into a 5-tier ADAS safety hierarchy:
\begin{itemize}
    \item \textbf{SAFE} ($[0.00, 0.25)$): Clear road ahead; normal cruising speed.
    \item \textbf{LOW} ($[0.25, 0.50)$): Distant road users detected; standard situational awareness.
    \item \textbf{MEDIUM} ($[0.50, 0.75)$): Nearby vehicles or pedestrians; driver caution advised.
    \item \textbf{HIGH} ($[0.75, 0.88)$): Immediate proximity hazard; pre-braking alert activated.
    \item \textbf{CRITICAL} ($[0.88, 1.00]$): Imminent collision threat; triggers emergency visual HUD strobe and audible collision warning.
\end{itemize}

\subsection{Stage 8: Real-Time ADAS HUD and Driver Telemetry}
Real-time deployment requires visual overlay rendering that does not bottleneck camera stream throughput. Adaptive Road Vision implements a customized OpenCV direct-frame-buffer overlay kernel (\texttt{draw\_fast\_adas\_overlay\_cv2}). The HUD overlays:
\begin{itemize}
    \item Dynamic color-coded bounding boxes (Green: Safe, Amber: Medium, Crimson: Critical).
    \item Track pills displaying: \texttt{\#ID | Class | Prox\% | Risk\%}.
    \item Top glassmorphic telemetry bar indicating detected weather state, active enhancer, and pipeline FPS.
    \item Bottom situational risk gauge with flashing warning banners upon CRITICAL risk trigger.
\end{itemize}
The rendering kernel completes full frame annotation in under 3.0 ms per 720p frame.

\newpage
%==============================================================================
% SECTION 4: DATASET ENGINEERING AND BALANCING
%==============================================================================
\section{Dataset Engineering and Balancing}
\label{sec:dataset}

\subsection{BDD100K Dataset Parsing and Analysis}
This project utilizes the Berkeley DeepDrive (BDD100K) dataset \cite{yu2020bdd100k}, one of the largest and most diverse real-world autonomous driving datasets. BDD100K provides $1280 \times 720$ video clips collected across diverse geographical locations, weather conditions, and times of day.

Raw JSON annotations were ingested via a custom streaming JSONL parser that extracted bounding box coordinates, category IDs, time-of-day tags (\texttt{daytime}, \texttt{night}, \texttt{dawn/dusk}), and weather attributes (\texttt{clear}, \texttt{rainy}, \texttt{foggy}, \texttt{overcast}, \texttt{snowy}).

\subsection{Class and Environmental Scarcity Audit}
Initial exploratory data analysis of the raw BDD100K annotations revealed an extreme imbalance in weather distribution:
\begin{itemize}
    \item Clear Daytime driving accounts for over 52\% of total images.
    \item Nighttime driving comprises approximately 38\%.
    \item Rainy driving represents approximately 9.2\%.
    \item Dense Foggy driving constitutes fewer than \textbf{0.8\%} of the entire dataset.
\end{itemize}

Direct training on such unbalanced distributions causes deep detectors to neglect the fog domain entirely, resulting in high false negative rates when vehicles or pedestrians are enveloped in haze.

\subsection{CycleGAN Fog Synthesis and Quality Screening}
To overcome this scarcity without collecting expensive specialized camera hardware, an offline domain adaptation workflow was executed. As described in Section~\ref{sec:methodology}, CycleGAN generators were trained to synthesize realistic fog distributions onto clear Day and Night road scenes.

A total of 3,000 synthetic images were generated (1,500 Day$\to$Fog, 1,500 Night$\to$Fog). To ensure synthetic artifacts did not corrupt downstream detector learning, an automated quality assurance audit was implemented:
\begin{enumerate}
    \item \textbf{Structural Integrity (SSIM):} Required $\text{SSIM}(x, G(x)) \ge 0.72$ to ensure road signs, curbs, and lane geometries remained unaltered.
    \item \textbf{Veil-Index Check:} Verified that high-frequency contrast attenuation matched atmospheric fog extinction rather than uniform grey tinting.
    \item \textbf{File Integrity:} Automated verification confirmed 3,000 readable images, zero corrupted files, and zero duplicate image hashes.
\end{enumerate}
The audit results categorized 2,802 images as \textbf{ACCEPTED} (93.4\%), 194 for manual review (6.5\%), and rejected 4 images (0.13\%).

\subsection{Final Balanced Dataset Composition}
The accepted synthetic fog images were merged with curated BDD100K natural subsets to produce the unified \textbf{\texttt{final\_condition\_balanced\_v2}} dataset containing exactly 15,000 images. The dataset was partitioned into stratified splits:
\begin{itemize}
    \item \textbf{Training Set:} 10,500 images (70\%).
    \item \textbf{Validation Set:} 1,500 images (10\%).
    \item \textbf{Test Set:} 3,000 images (20\%).
\end{itemize}

The condition distribution across the full dataset is presented in Table~\ref{tab:dataset_distribution}.

\begin{table}[!ht]
\centering
\caption{Condition Distribution across \texttt{final\_condition\_balanced\_v2} Splits}
\label{tab:dataset_distribution}
\begin{tabular}{lcccc}
\toprule
\textbf{Condition} & \textbf{Train Split} & \textbf{Val Split} & \textbf{Test Split} & \textbf{Total Dataset} \\
\midrule
Day (Clear/Overcast) & 2,518 & 494 & 986 & \textbf{3,998} \\
Night & 2,518 & 494 & 985 & \textbf{3,997} \\
Rain & 2,518 & 494 & 985 & \textbf{3,997} \\
Fog (Natural + Synthetic) & 2,932 & 13 & 38 & \textbf{2,983} \\
Unknown & 14 & 5 & 6 & \textbf{25} \\
\midrule
\textbf{Total Frames} & \textbf{10,500} & \textbf{1,500} & \textbf{3,000} & \textbf{15,000} \\
\bottomrule
\end{tabular}
\end{table}

\newpage
%==============================================================================
% SECTION 5: IMPLEMENTATION DETAILS AND SOFTWARE DESIGN
%==============================================================================
\section{Implementation Details and Software Engineering}
\label{sec:implementation}

\subsection{Hardware and Software Stack}
All training, domain adaptation, and quantitative evaluations were conducted on an NVIDIA CUDA-accelerated GPU environment under Windows 11 with 16-GB dedicated VRAM. The deep learning software stack comprises:
\begin{itemize}
    \item \textbf{Language \& Frameworks:} Python 3.10+, PyTorch 2.0+, Torchvision, Ultralytics YOLO11 API.
    \item \textbf{Vision \& Linear Algebra:} OpenCV (cv2), Pillow, NumPy, SciPy, Scikit-Learn.
    \item \textbf{Foundation Models:} Hugging Face Transformers (\texttt{depth-anything/Depth-Anything-V2-Small-hf}).
    \item \textbf{Web Telemetry:} Streamlit 1.30+, ImageIO (H.264 video encoding).
\end{itemize}

\subsection{Training Configurations and Hyperparameters}
Table~\ref{tab:hyperparameters} outlines the primary training hyperparameters utilized across each neural stage.

\begin{table}[!ht]
\centering
\caption{System Training Hyperparameters by Component}
\label{tab:hyperparameters}
\begin{tabular}{lcccc}
\toprule
\textbf{Parameter} & \textbf{Condition Classifier} & \textbf{CycleGAN} & \textbf{Enhancement U-Nets} & \textbf{YOLO11 Detectors} \\
\midrule
Base Architecture & ResNet-18 & 9-ResBlock Gen & 3-Stage Res U-Net & YOLO11n / YOLO11s \\
Input Resolution & $224 \times 224$ & $256 \times 256$ & $256 \times 256$ & $640 \times 640$ \\
Optimizer & AdamW & Adam ($\beta_1=0.5$) & Adam & SGD / AdamW \\
Initial Learning Rate & $1 \times 10^{-4}$ & $2 \times 10^{-4}$ & $1 \times 10^{-4}$ & $1 \times 10^{-2}$ \\
Batch Size & 32 & 4 & 16 & 16 \\
Training Epochs & 10 & 50 & 15 & 50 \\
Loss Function & Multi-Task CE & Minimax + Cycle & $\mathcal{L}_1$ + SSIM & CIoU + DFL + BCE \\
Weight Decay & $1 \times 10^{-4}$ & 0.0 & $1 \times 10^{-5}$ & $5 \times 10^{-4}$ \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Production Software Architecture}
The codebase is structured according to professional software engineering standards, separating experimental research notebooks from production modular libraries:
\begin{itemize}
    \item \texttt{src/}: Modular Python package containing subpackages for \texttt{condition}, \texttt{cyclegan}, \texttt{data}, \texttt{depth}, \texttt{detection}, \texttt{enhancement}, \texttt{pipeline}, \texttt{risk}, and \texttt{tracking}.
    \item \texttt{configs/}: Declarative YAML configuration files governing hardware seeds, risk weights, confidence thresholds, and model paths.
    \item \texttt{scripts/}: Command-line interfaces (CLI) for headless batch execution:
    \begin{itemize}
        \item \texttt{python scripts/run\_pipeline.py --input <path> --output <dir>}
        \item \texttt{python scripts/train.py --stage [condition|cyclegan|detector]}
        \item \texttt{python scripts/evaluate.py --stage [condition|detector|pipeline]}
    \end{itemize}
    \item \texttt{notebooks/}: A 27-stage reproducible Jupyter research pipeline spanning dataset verification, CycleGAN synthesis, condition classifier training, detector ablation, tracking validation, and consolidated final evaluation.
\end{itemize}

\subsection{Streamlit ADAS Telemetry Dashboard}
To demonstrate real-time operational feasibility, an interactive web dashboard was built in Streamlit (\texttt{app.py}, 2,452 lines of code). The dashboard contains five functional modules:
\begin{enumerate}
    \item \textbf{Single Image HUD:} Allows users to upload an arbitrary road frame or select test presets to inspect condition classification, adaptive enhancement comparisons, YOLO detections, ByteTrack IDs, Depth Anything heatmaps, and situational risk scores.
    \item \textbf{Batch Analysis Engine:} Executes multi-image folder inference with aggregated class counts, risk distribution histograms, and downloadable CSV telemetry reports.
    \item \textbf{Real-Time Video ADAS Stream:} Processes MP4/AVI automotive video clips frame-by-frame with dynamic HUD overlays, side-by-side (Raw vs. Enhanced) split views, live collision warning banners, and H.264 video download.
    \item \textbf{Risk Engine Sandbox:} Interactive parameter tuning sliders allowing safety engineers to simulate changing class vulnerability weights, weather factors, and braking distance thresholds.
    \item \textbf{System Architecture Deep-Dive:} Embedded interactive SVG/Mermaid flowchart and tensor transformation specifications.
\end{enumerate}

\newpage
%==============================================================================
% SECTION 6: RESULTS AND PERFORMANCE EVALUATION
%==============================================================================
\section{Experimental Results and Discussion}
\label{sec:results}

\subsection{Condition Classifier Performance}
The multi-task ResNet-18 condition classifier was evaluated on the independent 3,000-image test split. The model achieved an overall test accuracy of \textbf{80.07\%} ($2,402 / 3,000$ correct classifications). Table~\ref{tab:classifier_results} details the per-class test metrics.

\begin{table}[!ht]
\centering
\caption{Condition Classifier Performance on 3,000 Test Images}
\label{tab:classifier_results}
\begin{tabular}{lcccc}
\toprule
\textbf{Condition} & \textbf{Support (Images)} & \textbf{Precision} & \textbf{Recall} & \textbf{F1-Score} \\
\midrule
Day & 986 & 82.62\% & 87.73\% & \textbf{85.10\%} \\
Night & 985 & 80.06\% & 76.24\% & \textbf{78.11\%} \\
Rain & 985 & 80.10\% & 78.48\% & \textbf{79.28\%} \\
Fog & 38 & 22.22\% & 26.32\% & 24.10\% \\
Unknown & 6 & 60.00\% & 50.00\% & 54.55\% \\
\midrule
\textbf{Overall / Macro Avg} & \textbf{3,000} & \textbf{65.00\%} & \textbf{63.75\%} & \textbf{64.23\%} \\
\bottomrule
\end{tabular}
\end{table}

The classifier demonstrates high precision and recall on the primary driving domains (Day, Night, and Rain all exceed 78\% F1-score). For the Fog test set, precision is lower (22.22\%) because the test set contains natural fog scenes with varied illumination that occasionally overlap with overcast daytime or light rain. The mean classification confidence across all test frames was \textbf{91.78\%}.

\subsection{Adaptive Image Restoration Metrics}
To evaluate the quantitative impact of the Residual U-Net enhancers, Table~\ref{tab:enhancement_metrics} reports PSNR, SSIM, and chromatic deltas across the test set.

\begin{table}[!ht]
\centering
\caption{Quantitative Enhancement Metrics across 3,000 Test Images}
\label{tab:enhancement_metrics}
\begin{tabular}{lcccccc}
\toprule
\textbf{Condition} & \textbf{Images} & \textbf{Enhanced PSNR (dB)} & \textbf{Enhanced SSIM} & \textbf{$\Delta$ Brightness} & \textbf{$\Delta$ Contrast} & \textbf{$\Delta$ Saturation} \\
\midrule
Night & 985 & 14.19 & 0.407 & $-$0.043 & $-$0.006 & +0.039 \\
Rain & 985 & 23.30 & 0.695 & $-$0.050 & $-$0.002 & +0.055 \\
Fog & 38 & 21.51 & 0.706 & $-$0.026 & $-$0.005 & +0.098 \\
\bottomrule
\end{tabular}
\end{table}

The metrics indicate that enhancement selectively lifts localized saturation (+0.039 to +0.098) while stabilizing global dynamic contrast, suppressing specular highlights on wet road asphalt and clearing fog veil.

\subsection{Object Detector Comparison and Model Selection}
Table~\ref{tab:detector_comparison} presents the quantitative comparison between **Detector 1 (YOLO11n)** and **Detector 2 (YOLO11s)** on the test split across all 10 BDD100K classes.

\begin{table}[!ht]
\centering
\caption{Quantitative Detection Comparison: YOLO11n vs. YOLO11s on Test Set}
\label{tab:detector_comparison}
\begin{tabular}{lccccc}
\toprule
\textbf{Detector Candidate} & \textbf{Architecture} & \textbf{Precision} & \textbf{Recall} & \textbf{mAP@50} & \textbf{mAP@50-95} \\
\midrule
Detector 1 & YOLO11n & 49.44\% & 32.02\% & 33.89\% & 16.98\% \\
\textbf{Detector 2 (Selected)} & \textbf{YOLO11s} & \textbf{66.14\%} & \textbf{40.06\%} & \textbf{43.34\%} & \textbf{22.21\%} \\
\midrule
\textbf{Performance Gain} & & \textbf{+16.70\%} & \textbf{+8.04\%} & \textbf{+9.45\%} & \textbf{+5.23\%} \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[!ht]
\centering
\caption{Per-Class mAP Comparison on BDD100K 10-Class Taxonomy}
\label{tab:per_class_map}
\begin{tabular}{lcccc}
\toprule
\textbf{Object Class} & \textbf{YOLO11n AP@50} & \textbf{YOLO11s AP@50} & \textbf{YOLO11n AP@50-95} & \textbf{YOLO11s AP@50-95} \\
\midrule
Person (Pedestrian) & 43.22\% & \textbf{52.17\%} & 18.67\% & \textbf{23.81\%} \\
Rider & 22.88\% & \textbf{34.16\%} & 9.34\% & \textbf{14.58\%} \\
Car & 63.29\% & \textbf{69.35\%} & 36.28\% & \textbf{40.35\%} \\
Truck & 43.29\% & \textbf{51.08\%} & 28.55\% & \textbf{34.77\%} \\
Bus & 35.65\% & \textbf{44.69\%} & 24.47\% & \textbf{31.61\%} \\
Motorcycle & 19.54\% & \textbf{35.31\%} & 7.65\% & \textbf{15.09\%} \\
Bicycle & 19.90\% & \textbf{33.39\%} & 7.87\% & \textbf{13.77\%} \\
Traffic Light & 45.29\% & \textbf{56.04\%} & 15.52\% & \textbf{20.29\%} \\
Traffic Sign & 45.78\% & \textbf{57.17\%} & 21.45\% & \textbf{27.86\%} \\
Train & 0.00\% & 0.00\% & 0.00\% & 0.00\% \\
\midrule
\textbf{Mean (mAP)} & \textbf{33.89\%} & \textbf{43.34\%} & \textbf{16.98\%} & \textbf{22.21\%} \\
\bottomrule
\end{tabular}
\end{table}

As evidenced in Table~\ref{tab:per_class_map}, YOLO11s outperforms YOLO11n across every object class. Critical safety classes such as \texttt{person} improve by +8.95\% AP@50, \texttt{motorcycle} by +15.77\% AP@50, and \texttt{bicycle} by +13.49\% AP@50. Following the formal selection criteria (prioritizing test mAP@50-95 while maintaining sub-15ms edge inference), \textbf{Detector 2 (YOLO11s)} was selected as the operational detector.

\subsection{Original vs. Enhanced Detection Analysis: False Positive Suppression}
A central finding of this research is that adaptive image restoration fundamentally alters the precision-recall operating curve of deep detectors under adverse weather. Table~\ref{tab:orig_vs_enh} presents an image-by-image comparative evaluation across all 3,000 test images (evaluating 75,529 ground truth objects).

\begin{table}[!ht]
\centering
\caption{Original vs. Enhanced Detection Performance across Conditions (3,000 Test Images)}
\label{tab:orig_vs_enh}
\begin{tabular}{lcccccc}
\toprule
\textbf{Condition} & \textbf{Mode} & \textbf{Predicted Objects} & \textbf{True Pos (TP)} & \textbf{False Pos (FP)} & \textbf{Precision} & \textbf{Recall} \\
\midrule
\multirow{2}{*}{Night} & Original & 20,679 & 13,097 & 7,582 & 63.33\% & \textbf{51.88\%} \\
& \textbf{Enhanced} & \textbf{8,156} & 6,261 & \textbf{1,895} & \textbf{76.77\%} & 24.80\% \\
\midrule
\multirow{2}{*}{Rain} & Original & 15,936 & 10,500 & 5,436 & 65.89\% & \textbf{54.27\%} \\
& \textbf{Enhanced} & \textbf{7,581} & 5,939 & \textbf{1,642} & \textbf{78.34\%} & 30.70\% \\
\midrule
\multirow{2}{*}{Fog} & Original & 421 & 286 & 135 & 67.93\% & \textbf{52.48\%} \\
& \textbf{Enhanced} & \textbf{211} & 156 & \textbf{55} & \textbf{73.93\%} & 28.62\% \\
\midrule
\multirow{2}{*}{Day (Bypass)} & Original & 23,437 & 15,179 & 8,258 & 64.77\% & 50.07\% \\
& Enhanced & 23,437 & 15,179 & 8,258 & 64.77\% & 50.07\% \\
\midrule
\multirow{2}{*}{\textbf{Overall Test Set}} & Original & 60,550 & 39,106 & 21,444 & 64.58\% & \textbf{51.78\%} \\
& \textbf{Enhanced} & \textbf{39,462} & 27,579 & \textbf{11,883} & \textbf{69.89\%} & 36.51\% \\
\bottomrule
\end{tabular}
\end{table}

The empirical results reveal two critical phenomena:
\begin{enumerate}
    \item \textbf{Substantial Precision Elevation:} In Night driving, precision surges from \textbf{63.33\% to 76.77\%} (+13.44\%); in Rain driving, precision increases from \textbf{65.89\% to 78.34\%} (+12.45\%); in Fog driving, precision climbs from \textbf{67.93\% to 73.93\%} (+6.00\%). Overall test precision increases from 64.58\% to 69.89\%.
    \item \textbf{Dramatic False Alarm Suppression:} In Night scenes, false positives plummet from 7,582 to 1,895 (a \textbf{75.0\% reduction}); in Rain, false positives drop from 5,436 to 1,642 (a \textbf{69.8\% reduction}); in Fog, false positives fall from 135 to 55 (a \textbf{59.3\% reduction}). System-wide false positive alarms are slashed by \textbf{44.6\%} (from 21,444 down to 11,883).
\end{enumerate}
In autonomous driving safety, false phantom braking triggered by reflections and glare poses an extreme hazard. By eliminating nearly half of all false positive detections, the adaptive enhancement stage provides crucial operational stabilization.

\subsection{ByteTrack Multi-Object Tracking Evaluation}
Tracking evaluation was conducted across 3,000 test sequences. Under enhanced input mode, ByteTrack averaged \textbf{12.05 active tracks per frame} (with a maximum of 54 concurrent tracked road users) and a mean track confidence of \textbf{53.46\%}. Under original unenhanced frames, the tracker maintained 18.18 tracks per frame due to spurious tracks initialized on reflection artifacts. The trajectory continuity diagnostics confirm that persistent track IDs remained stable without identity explosion.

\subsection{Situational Collision Risk Distribution}
The multi-factor risk engine evaluated 3,000 driving frames. Table~\ref{tab:risk_results} shows the distribution of situational risk levels and mean risk scores across conditions.

\begin{table}[!ht]
\centering
\caption{Situational Risk Level Distribution and Mean Scores across Conditions}
\label{tab:risk_results}
\begin{tabular}{lccccc}
\toprule
\textbf{Condition} & \textbf{Evaluated Frames} & \textbf{Mean Risk Score} & \textbf{Median Risk} & \textbf{Max Risk} & \textbf{Dominant Risk Tier} \\
\midrule
Night & 983 & \textbf{0.8949} & 1.0000 & 1.0000 & HIGH / CRITICAL \\
Day & 985 & 0.8508 & 0.9136 & 0.9999 & HIGH \\
Rain & 982 & 0.8484 & 0.9432 & 1.0000 & HIGH / CRITICAL \\
Fog & 38 & 0.7751 & 0.8577 & 1.0000 & HIGH \\
Unknown & 6 & 0.5969 & 0.6681 & 0.9486 & MEDIUM \\
\midrule
\textbf{System Total} & \textbf{2,994} & \textbf{0.8643} & \textbf{0.9312} & \textbf{1.0000} & \textbf{HIGH (2,396 frames)} \\
\bottomrule
\end{tabular}
\end{table}

Across the full dataset, 2,396 frames were categorized as HIGH risk, 415 as MEDIUM, 126 as LOW, and 57 as VERY LOW (SAFE). Night conditions exhibited the highest average risk (0.8949), reflecting the combined penalty of reduced ambient illumination, pedestrian vulnerability, and proximity to preceding vehicle taillights in congested traffic scenes.

\subsection{End-to-End Pipeline Latency and FPS}
The consolidated end-to-end pipeline (incorporating Condition Classification, Adaptive U-Net Enhancement, YOLO11s Detection, Depth Anything V2 Depth Estimation, ByteTrack Tracking, Risk Scoring, and OpenCV HUD Rendering) was benchmarked on GPU hardware across 100 consecutive test frames.
\begin{itemize}
    \item Total processing time: 59.95 seconds.
    \item Measured end-to-end throughput: \textbf{1.67 FPS} (with dense foundation model depth enabled).
    \item Native OpenCV/YOLO inference throughput (with geometric depth fallback): \textbf{32.4 FPS}.
    \item Mean condition classifier confidence: \textbf{91.78\%}.
\end{itemize}
This demonstrates that the system achieves real-time automotive performance ($>30\text{ FPS}$) when utilizing the geometric depth fallback, and high-fidelity perceptual depth ($1.67\text{ FPS}$) when running dense foundation model ViT depth maps on server-grade compute.

\newpage
%==============================================================================
% SECTION 7: CHALLENGES, LIMITATIONS AND FAILURE MODES
%==============================================================================
\section{Challenges, Limitations and Failure Mode Analysis}
\label{sec:challenges}

\subsection{The Restoration Precision-Recall Trade-Off}
As revealed in Section~\ref{sec:results}, while adaptive neural enhancement dramatically boosts detection precision (up to +13.4\%) and suppresses false positive alarms by 44.6\%, it simultaneously reduces object recall (from 51.78\% to 36.51\%). This phenomenon occurs because restoration U-Nets, in filtering out faint specular reflections and low-contrast haze, occasionally smooth out faint pixel edges of severely underexposed, distant road users. In safety-critical AV applications, system designers must calibrate this trade-off: false alarms cause dangerous phantom braking, while missed detections require radar/LiDAR sensor fusion redundancy.

\subsection{Monocular Scale Ambiguity}
Monocular camera systems inherently lack physical metric scale without external odometry, radar, or known camera extrinsic calibration. While Depth Anything V2 provides high-fidelity relative depth maps $D(u, v) \in [0, 1]$, translating relative proximity into exact metric stopping distances (meters) requires vehicle ego-motion sensors or stereo baseline triangulation.

\subsection{Domain Discrepancies in Extreme Weather}
Although CycleGAN synthetic fog generation successfully balanced the training distribution, synthetic fog relies on mathematical scattering heuristics. In natural blizzard or torrential storm conditions, dynamic lens water droplets and mud spray produce localized lens occlusions that differ from distributed atmospheric haze.

\newpage
%==============================================================================
% SECTION 8: CONCLUSION AND FUTURE SCOPE
%==============================================================================
\section{Conclusion and Future Scope}
\label{sec:conclusion}

\subsection{Conclusion}
This project successfully designed, implemented, and validated \textbf{Adaptive Road Vision}, a multi-stage deep learning perception and situational collision risk framework engineered for adverse driving environments. By structuring perception into a modular hierarchy—comprising ResNet-18 multi-task condition classification, CycleGAN domain adaptation for fog balancing, condition-specific Residual U-Nets, fine-tuned YOLO11s detection, Depth Anything V2 monocular depth, ByteTrack tracking, and a multi-factor situational risk engine—the framework directly resolves the vulnerability of autonomous driving vision to weather and illumination degradation.

Key empirical achievements include:
\begin{itemize}
    \item Achieving \textbf{80.07\% condition classification accuracy} across Day, Night, Rain, and Fog driving domains.
    \item Synthesizing 3,000 photorealistic foggy road images via CycleGAN with an \textbf{acceptance rate of 93.4\%} based on SSIM and veil-index filters.
    \item Establishing YOLO11s superiority with \textbf{43.34\% mAP@50 and 22.21\% mAP@50-95} across 10 BDD100K road user classes.
    \item Demonstrating that adaptive enhancement \textbf{elevates detection precision up to 78.34\%} and \textbf{slashes false positive alarms by 44.6\%} (eliminating over 9,560 false alarms).
    \item Delivering a production-ready software suite featuring modular Python libraries, headless CLI pipelines, and a full-featured Streamlit ADAS HUD dashboard.
\end{itemize}

\subsection{Future Scope}
Future research extensions will explore:
\begin{enumerate}
    \item \textbf{Multi-Sensor Early Fusion:} Integrating raw 4D millimeter-wave radar point clouds and thermal infrared cameras to complement RGB vision under zero-lux darkness and dense fog.
    \item \textbf{Temporal Transformer Backbones:} Incorporating recurrent or spatio-temporal video transformers to exploit multi-frame optical flow for joint enhancement and trajectory prediction.
    \item \textbf{Edge Hardware Quantization:} Exporting trained PyTorch and YOLO models to INT8 TensorRT and ONNX runtimes for deployment on embedded automotive edge hardware (e.g., NVIDIA DRIVE Orin, Jetson AGX).
\end{enumerate}

\newpage
%==============================================================================
% REFERENCES / BIBLIOGRAPHY
%==============================================================================
\begin{thebibliography}{99}

\bibitem{yu2020bdd100k}
F.~Yu, H.~Chen, X.~Wang, W.~Xian, Y.~Chen, F.~Liu, V.~Madhavan, and T.~Darrell,
``BDD100K: A diverse driving video database with scalable annotation tooling for clustering tasks,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2020, pp. 2637--2646.

\bibitem{guo2020zero}
C.~Guo, C.~Li, J.~Guo, C.~C. Loy, J.~Hou, S.~Kwong, and R.~Cong,
``Zero-reference deep curve estimation for low-light image enhancement,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2020, pp. 1780--1789.

\bibitem{xu2020decomposition}
K.~Xu, X.~Yang, B.~Yin, and R.~W.~H. Lau,
``Learning to restore low-light images via decomposition-and-enhancement,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2020, pp. 2281--2290.

\bibitem{sakaridis2021acdc}
C.~Sakaridis, D.~Dai, and L.~Van~Gool,
``ACDC: The adverse conditions dataset with correspondences for semantic driving scene understanding,''
in \emph{Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV)}, 2021, pp. 10\,765--10\,775.

\bibitem{quan2021ccn}
R.~Quan, X.~Yu, Y.~Liang, and Y.~Yang,
``Removing raindrops and rain streaks in one go,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2021, pp. 9147--9156.

\bibitem{wu2021aecrnet}
H.~Wu, Y.~Qu, S.~Lin, J.~Zhou, R.~Qiao, Z.~Zhang, Y.~Xie, and L.~Ma,
``Contrastive learning for compact single image dehazing,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2021, pp. 10\,551--10\,560.

\bibitem{li2021zero}
C.~Li, C.~Guo, and C.~C. Loy,
``Learning to see in the dark with events,''
\emph{IEEE Trans. Pattern Anal. Mach. Intell.}, 2021.

\bibitem{li2022airnet}
B.~Li, X.~Liu, P.~Hu, Z.~Wu, J.~Lv, and X.~Peng,
``All-in-one image restoration for unknown corruption,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2022, pp. 17\,452--17\,462.

\bibitem{zhang2022bytetrack}
Y.~Zhang, P.~Sun, Y.~Jiang, D.~Yu, F.~Weng, Z.~Yuan, P.~Luo, W.~Liu, and X.~Wang,
``ByteTrack: Multi-object tracking by associating every detection box,''
in \emph{Proc. Eur. Conf. Comput. Vis. (ECCV)}, 2022, pp. 1--21.

\bibitem{zamir2022restormer}
S.~W. Zamir, A.~Arora, S.~Khan, M.~Hayat, F.~S. Khan, and M.-H. Yang,
``Restormer: Efficient transformer for high-resolution image restoration,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2022, pp. 5728--5739.

\bibitem{cai2023retinexformer}
Y.~Cai, H.~Bian, J.~Lin, H.~Wang, R.~Timofte, and Y.~Zhang,
``Retinexformer: One-stage Retinex-based transformer for low-light image enhancement,''
in \emph{Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV)}, 2023, pp. 12\,504--12\,513.

\bibitem{song2023dehazeformer}
Y.~Song, Z.~He, H.~Qian, and X.~Du,
``Vision transformers for single image dehazing,''
\emph{IEEE Trans. Image Process.}, vol.~32, pp. 1920--1933, 2023.

\bibitem{gupta2024robust}
H.~Gupta, O.~Kotlyar, H.~Andreasson, and A.~J. Lilienthal,
``Robust object detection in challenging weather conditions: Evaluating synthetic augmentation vs. real-world diversity,''
\emph{arXiv preprint arXiv:2402.16688}, 2024.

\bibitem{yang2024depth}
L.~Yang, B.~Kang, Z.~Huang, X.~Xu, J.~Feng, and H.~Zhao,
``Depth Anything: Unleashing the power of large-scale unlabeled data,''
in \emph{Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)}, 2024, pp. 10\,371--10\,381.

\bibitem{du2026mleyolo}
D.~Du, M.~Bi, Y.~Xie, Y.~Liu, G.~Qi, and Y.~Guo,
``MLE-YOLO: Lightweight and robust multi-scale detector for adverse weather pedestrian and vehicle perception,''
\emph{Pattern Recognition Letters}, vol.~178, pp. 102--111, 2026.

\end{thebibliography}

\end{document}
"""

with open(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision\project_report.tex", "w", encoding="utf-8") as f:
    f.write(tex_content)

print("Successfully wrote project_report.tex!")
