import os
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
from PIL import Image
import cv2
import csv
from os.path import join

from nets.unet import Unet
from utils.dataloader import UnetDataset


def Iou_score(smooth=1e-5, threshold=0.5):
    """
    IoU score calculation function for model compilation
    """

    def _Iou_score(y_true, y_pred):
        # score calculation
        y_pred = tf.keras.backend.greater(y_pred, threshold)
        y_pred = tf.keras.backend.cast(y_pred, tf.keras.backend.floatx())
        intersection = tf.keras.backend.sum(y_true[..., :-1] * y_pred, axis=[0, 1, 2])
        union = tf.keras.backend.sum(y_true[..., :-1] + y_pred, axis=[0, 1, 2]) - intersection

        score = (intersection + smooth) / (union + smooth)
        return score

    return _Iou_score


def f_score(beta=1, smooth=1e-5, threshold=0.5):
    """
    F-score calculation function for model compilation
    """

    def _f_score(y_true, y_pred):
        y_pred = tf.keras.backend.greater(y_pred, threshold)
        y_pred = tf.keras.backend.cast(y_pred, tf.keras.backend.floatx())

        tp = tf.keras.backend.sum(y_true[..., :-1] * y_pred, axis=[0, 1, 2])
        fp = tf.keras.backend.sum(y_pred, axis=[0, 1, 2]) - tp
        fn = tf.keras.backend.sum(y_true[..., :-1], axis=[0, 1, 2]) - tp

        score = ((1 + beta ** 2) * tp + smooth) / \
                ((1 + beta ** 2) * tp + beta ** 2 * fn + fp + smooth)
        return score

    return _f_score


def fast_hist(a, b, n):
    """
    Compute confusion matrix

    Args:
        a: flattened ground truth array (H×W,)
        b: flattened prediction array (H×W,)
        n: number of classes

    Returns:
        Confusion matrix of shape (n, n)
    """
    k = (a >= 0) & (a < n)
    return np.bincount(n * a[k].astype(int) + b[k], minlength=n ** 2).reshape(n, n)


def per_class_iu(hist):
    """Calculate IoU for each class from confusion matrix"""
    return np.diag(hist) / np.maximum((hist.sum(1) + hist.sum(0) - np.diag(hist)), 1)


def per_class_PA_Recall(hist):
    """Calculate recall/pixel accuracy for each class from confusion matrix"""
    return np.diag(hist) / np.maximum(hist.sum(1), 1)


def per_class_Precision(hist):
    """Calculate precision for each class from confusion matrix"""
    return np.diag(hist) / np.maximum(hist.sum(0), 1)


def per_Accuracy(hist):
    """Calculate global accuracy from confusion matrix"""
    return np.sum(np.diag(hist)) / np.maximum(np.sum(hist), 1)


def compute_f1(hist):
    """
    Calculate F1 scores for each class from confusion matrix

    Args:
        hist: confusion matrix of shape (n_classes, n_classes)

    Returns:
        f1_scores: F1 score for each class
        mean_f1: mean F1 score
    """
    precision = per_class_Precision(hist)
    recall = per_class_PA_Recall(hist)

    # Calculate F1 score for each class
    f1_scores = 2 * precision * recall / np.maximum((precision + recall), 1e-5)

    # Calculate mean F1 score across all classes
    mean_f1 = np.nanmean(f1_scores)

    return f1_scores, mean_f1


def compute_mIoU(gt_dir=None, pred_dir=None, png_name_list=None, num_classes=None, name_classes=None, hist=None):
    """
    Compute mIoU metrics given either:
    1. Paths to ground truth and prediction images OR
    2. A precomputed confusion matrix (hist)

    Args:
        gt_dir: directory containing ground truth images
        pred_dir: directory containing prediction images
        png_name_list: list of image names (without extension)
        num_classes: number of classes
        name_classes: list of class names
        hist: precomputed confusion matrix (optional)

    Returns:
        hist: confusion matrix
        IoUs: IoU for each class
        PA_Recall: pixel accuracy/recall for each class
        Precision: precision for each class
    """
    if hist is None:
        if gt_dir is None or pred_dir is None or png_name_list is None or num_classes is None:
            raise ValueError("Either provide hist or (gt_dir, pred_dir, png_name_list, num_classes)")

        print('Num classes', num_classes)
        hist = np.zeros((num_classes, num_classes))

        gt_imgs = [join(gt_dir, x + ".png") for x in png_name_list]
        pred_imgs = [join(pred_dir, x + ".png") for x in png_name_list]

        for ind in range(len(gt_imgs)):
            pred = np.array(Image.open(pred_imgs[ind]))
            label = np.array(Image.open(gt_imgs[ind]))

            if len(label.flatten()) != len(pred.flatten()):
                print(
                    'Skipping: len(gt) = {:d}, len(pred) = {:d}, {:s}, {:s}'.format(
                        len(label.flatten()), len(pred.flatten()), gt_imgs[ind],
                        pred_imgs[ind]))
                continue

            hist += fast_hist(label.flatten(), pred.flatten(), num_classes)

            if name_classes is not None and ind > 0 and ind % 10 == 0:
                print('{:d} / {:d}: mIou-{:0.2f}%; mPA-{:0.2f}%; Accuracy-{:0.2f}%'.format(
                    ind,
                    len(gt_imgs),
                    100 * np.nanmean(per_class_iu(hist)),
                    100 * np.nanmean(per_class_PA_Recall(hist)),
                    100 * per_Accuracy(hist)
                )
                )

    # Calculate metrics
    IoUs = per_class_iu(hist)
    PA_Recall = per_class_PA_Recall(hist)
    Precision = per_class_Precision(hist)

    # Print per-class metrics if class names are provided
    if name_classes is not None:
        for ind_class in range(len(name_classes)):
            print('===>' + name_classes[ind_class] + ':\tIou-' + str(round(IoUs[ind_class] * 100, 2)) \
                  + '; Recall (equal to the PA)-' + str(round(PA_Recall[ind_class] * 100, 2)) + '; Precision-' + str(
                round(Precision[ind_class] * 100, 2)))

    # Print overall metrics
    print('===> mIoU: ' + str(round(np.nanmean(IoUs) * 100, 2)) +
          '; mPA: ' + str(round(np.nanmean(PA_Recall) * 100, 2)) +
          '; Accuracy: ' + str(round(per_Accuracy(hist) * 100, 2)))

    return hist, IoUs, PA_Recall, Precision


def calculate_confusion_matrix(gt_list, pred_list, num_classes):
    """
    Calculate confusion matrix from lists of ground truth and prediction arrays

    Args:
        gt_list: list of ground truth arrays
        pred_list: list of prediction arrays
        num_classes: number of classes

    Returns:
        hist: confusion matrix
    """
    hist = np.zeros((num_classes, num_classes))

    for i in range(len(gt_list)):
        hist += fast_hist(gt_list[i].flatten(), pred_list[i].flatten(), num_classes)

    return hist


def adjust_axes(r, t, fig, axes):
    """Adjust figure axes to fit text"""
    bb = t.get_window_extent(renderer=r)
    text_width_inches = bb.width / fig.dpi
    current_fig_width = fig.get_figwidth()
    new_fig_width = current_fig_width + text_width_inches
    proportion = new_fig_width / current_fig_width
    x_lim = axes.get_xlim()
    axes.set_xlim([x_lim[0], x_lim[1] * proportion])


def draw_plot_func(values, name_classes, plot_title, x_label, output_path, tick_font_size=12, plt_show=True):
    """Create bar chart for metrics visualization"""
    fig = plt.gcf()
    axes = plt.gca()
    plt.barh(range(len(values)), values, color='royalblue')
    plt.title(plot_title, fontsize=tick_font_size + 2)
    plt.xlabel(x_label, fontsize=tick_font_size)
    plt.yticks(range(len(values)), name_classes, fontsize=tick_font_size)
    r = fig.canvas.get_renderer()
    for i, val in enumerate(values):
        str_val = " " + str(val)
        if val < 1.0:
            str_val = " {0:.2f}".format(val)
        t = plt.text(val, i, str_val, color='royalblue', va='center', fontweight='bold')
        if i == (len(values) - 1):
            adjust_axes(r, t, fig, axes)

    fig.tight_layout()
    fig.savefig(output_path)
    if plt_show:
        plt.show()
    plt.close()


def show_results(miou_out_path, hist, IoUs, PA_Recall, Precision, name_classes, tick_font_size=12):
    """Visualize and save evaluation metrics"""
    # Create metric visualization plots
    draw_plot_func(IoUs, name_classes, "mIoU = {0:.2f}%".format(np.nanmean(IoUs) * 100), "Intersection over Union",
                   os.path.join(miou_out_path, "mIoU.png"), tick_font_size=tick_font_size, plt_show=False)
    print("Save mIoU out to " + os.path.join(miou_out_path, "mIoU.png"))

    draw_plot_func(PA_Recall, name_classes, "mPA = {0:.2f}%".format(np.nanmean(PA_Recall) * 100), "Pixel Accuracy",
                   os.path.join(miou_out_path, "mPA.png"), tick_font_size=tick_font_size, plt_show=False)
    print("Save mPA out to " + os.path.join(miou_out_path, "mPA.png"))

    draw_plot_func(PA_Recall, name_classes, "mRecall = {0:.2f}%".format(np.nanmean(PA_Recall) * 100), "Recall",
                   os.path.join(miou_out_path, "Recall.png"), tick_font_size=tick_font_size, plt_show=False)
    print("Save Recall out to " + os.path.join(miou_out_path, "Recall.png"))

    draw_plot_func(Precision, name_classes, "mPrecision = {0:.2f}%".format(np.nanmean(Precision) * 100), "Precision",
                   os.path.join(miou_out_path, "Precision.png"), tick_font_size=tick_font_size, plt_show=False)
    print("Save Precision out to " + os.path.join(miou_out_path, "Precision.png"))

    # Save confusion matrix to CSV
    with open(os.path.join(miou_out_path, "confusion_matrix.csv"), 'w', newline='') as f:
        writer = csv.writer(f)
        writer_list = []
        writer_list.append([' '] + [str(c) for c in name_classes])
        for i in range(len(hist)):
            writer_list.append([name_classes[i]] + [str(x) for x in hist[i]])
        writer.writerows(writer_list)
    print("Save confusion_matrix out to " + os.path.join(miou_out_path, "confusion_matrix.csv"))

    # Calculate and save F1 scores
    f1_scores, mean_f1 = compute_f1(hist)
    draw_plot_func(f1_scores, name_classes, "mF1 = {0:.2f}%".format(mean_f1 * 100), "F1 Score",
                   os.path.join(miou_out_path, "F1.png"), tick_font_size=tick_font_size, plt_show=False)
    print("Save F1 out to " + os.path.join(miou_out_path, "F1.png"))

    # Save all metrics to a text file
    with open(os.path.join(miou_out_path, "evaluation_results.txt"), 'w') as f:
        f.write(f"mIoU: {np.nanmean(IoUs):.4f}\n")
        f.write(f"Mean F1-Score: {mean_f1:.4f}\n")
        f.write(f"Mean Precision: {np.nanmean(Precision):.4f}\n")
        f.write(f"Mean Recall: {np.nanmean(PA_Recall):.4f}\n")
        f.write(f"Global Accuracy: {per_Accuracy(hist):.4f}\n\n")

        f.write("Per-class metrics:\n")
        for i in range(len(name_classes)):
            f.write(f"Class {i} ({name_classes[i]}):\n")
            f.write(f"  IoU: {IoUs[i]:.4f}\n")
            f.write(f"  F1: {f1_scores[i]:.4f}\n")
            f.write(f"  Precision: {Precision[i]:.4f}\n")
            f.write(f"  Recall: {PA_Recall[i]:.4f}\n\n")

    return mean_f1


def evaluate(
        model_path,
        input_shape,
        num_classes,
        backbone,
        dataset_path,
        batch_size=1,
        miou_out_path="miou_out",
        show=False,
        mode="evaluate",
        class_names=None
):
    """
    Evaluate model performance

    Args:
        model_path: path to model weights
        input_shape: input shape [height, width]
        num_classes: number of classes (including background)
        backbone: backbone network ('vgg' or 'resnet50')
        dataset_path: dataset path
        batch_size: batch size for evaluation
        miou_out_path: output path for evaluation results
        show: whether to display prediction results
        mode: 'evaluate' for full validation set, 'predict' for sample images
        class_names: list of class names (optional)

    Returns:
        mIoU: mean IoU
        mf1: mean F1 score
    """
    # Set default class names if not provided
    if class_names is None:
        class_names = [f"Class {i}" for i in range(num_classes)]

    # Create output directories
    if not os.path.exists(miou_out_path):
        os.makedirs(miou_out_path)
        os.makedirs(os.path.join(miou_out_path, 'images'))
        os.makedirs(os.path.join(miou_out_path, 'pred'))
        os.makedirs(os.path.join(miou_out_path, 'ground_truth'))

    # Load model
    model = Unet([input_shape[0], input_shape[1], 3], num_classes, backbone)
    model.load_weights(model_path)
    print(f"Model loaded successfully: {model_path}")

    # Read validation set file list
    with open(os.path.join(dataset_path, "VOC2007/ImageSets/Segmentation/val.txt"), "r") as f:
        val_lines = f.readlines()
    num_val = len(val_lines)

    if mode == "evaluate":
        print(f"Evaluating the entire validation set ({num_val} images)...")

        # Create directories for evaluation results
        pred_dir = os.path.join(miou_out_path, 'detection-results')
        gt_dir = os.path.join(miou_out_path, 'ground-truth')

        if not os.path.exists(pred_dir):
            os.makedirs(pred_dir)
        if not os.path.exists(gt_dir):
            os.makedirs(gt_dir)

        print("Starting prediction...")
        total_pred = []
        total_gt = []
        png_name_list = []

        for i in range(num_val):
            if i % 100 == 0:
                print(f"Processed {i}/{num_val} images")

            # Get image and label paths
            img_name = val_lines[i].strip()
            png_name_list.append(img_name)
            img_path = os.path.join(dataset_path, f"VOC2007/JPEGImages/{img_name}.jpg")
            label_path = os.path.join(dataset_path, f"VOC2007/SegmentationClass/{img_name}.png")

            # Read and preprocess image
            image = Image.open(img_path)
            old_img = np.array(image)
            original_h = np.array(image).shape[0]
            original_w = np.array(image).shape[1]

            # Resize image to model input shape
            image = image.resize((input_shape[1], input_shape[0]), Image.BILINEAR)
            img = np.array(image) / 255.0
            img = np.expand_dims(img, axis=0)

            # Model prediction
            pr = model.predict(img)[0]
            pr = pr.argmax(axis=-1)

            # Resize prediction back to original size
            pr = pr.reshape((input_shape[0], input_shape[1]))
            pr = cv2.resize(np.uint8(pr), (original_w, original_h), interpolation=cv2.INTER_NEAREST)

            # Create prediction mask
            pred_mask = np.zeros((original_h, original_w), dtype=np.uint8)
            for c in range(num_classes):
                pred_mask[pr == c] = c

            # Save prediction mask
            pred_img = Image.fromarray(pred_mask.astype(np.uint8))
            pred_img.save(os.path.join(pred_dir, f"{img_name}.png"))

            total_pred.append(pred_mask)

            # Read and save ground truth
            label = np.array(Image.open(label_path))
            gt_img = Image.fromarray(label.astype(np.uint8))
            gt_img.save(os.path.join(gt_dir, f"{img_name}.png"))
            total_gt.append(label)

            # Save visualization for sample images
            if show and i < 10:  # Only show first 10 results
                fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                axes[0].imshow(old_img)
                axes[0].set_title('Original Image')
                axes[0].axis('off')

                axes[1].imshow(label, cmap='viridis')
                axes[1].set_title('Ground Truth')
                axes[1].axis('off')

                axes[2].imshow(pred_mask, cmap='viridis')
                axes[2].set_title('Prediction')
                axes[2].axis('off')

                plt.tight_layout()
                plt.savefig(os.path.join(miou_out_path, f'images/comparison_{img_name}.png'))
                if show:
                    plt.show()
                plt.close()

        print("Prediction complete, calculating metrics...")

        # Calculate confusion matrix
        hist = calculate_confusion_matrix(total_gt, total_pred, num_classes)

        # Calculate metrics
        _, IoUs, PA_Recall, Precision = compute_mIoU(hist=hist)
        mIoU = np.nanmean(IoUs)

        # Calculate F1 scores
        f1_scores, mf1 = compute_f1(hist)

        # Show and save results
        show_results(miou_out_path, hist, IoUs, PA_Recall, Precision, class_names, tick_font_size=12)

        return mIoU, mf1

    elif mode == "predict":
        # Single image prediction mode
        import random
        sample_indices = random.sample(range(num_val), min(5, num_val))

        for idx in sample_indices:
            img_name = val_lines[idx].strip()
            img_path = os.path.join(dataset_path, f"VOC2007/JPEGImages/{img_name}.jpg")
            label_path = os.path.join(dataset_path, f"VOC2007/SegmentationClass/{img_name}.png")

            # Predict single image
            image = Image.open(img_path)
            old_img = np.array(image)
            original_h = np.array(image).shape[0]
            original_w = np.array(image).shape[1]

            image = image.resize((input_shape[1], input_shape[0]), Image.BILINEAR)
            img = np.array(image) / 255.0
            img = np.expand_dims(img, axis=0)

            # Model prediction
            pr = model.predict(img)[0]
            pr = pr.argmax(axis=-1)

            # Resize prediction back to original size
            pr = pr.reshape((input_shape[0], input_shape[1]))
            pr = cv2.resize(np.uint8(pr), (original_w, original_h), interpolation=cv2.INTER_NEAREST)

            # Create prediction mask
            pred_mask = np.zeros((original_h, original_w), dtype=np.uint8)
            for c in range(num_classes):
                pred_mask[pr == c] = c

            # Read ground truth
            label = np.array(Image.open(label_path))

            # Create visualization
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            axes[0].imshow(old_img)
            axes[0].set_title('Original Image')
            axes[0].axis('off')

            axes[1].imshow(label, cmap='viridis')
            axes[1].set_title('Ground Truth')
            axes[1].axis('off')

            axes[2].imshow(pred_mask, cmap='viridis')
            axes[2].set_title('Prediction')
            axes[2].axis('off')

            plt.tight_layout()
            plt.savefig(os.path.join(miou_out_path, f'images/predict_{img_name}.png'))
            if show:
                plt.show()
            plt.close()

            # Calculate metrics for single image
            hist = calculate_confusion_matrix([label], [pred_mask], num_classes)
            IoUs = per_class_iu(hist)
            mIoU = np.nanmean(IoUs)
            f1_scores, mf1 = compute_f1(hist)

            print(f"Image {img_name}:")
            print(f"  mIoU: {mIoU:.4f}")
            print(f"  Mean F1-Score: {mf1:.4f}")

            # Print per-class metrics
            for c in range(num_classes):
                class_name = class_names[c] if c < len(class_names) else f"Class {c}"
                print(f"  {class_name} - IoU: {IoUs[c]:.4f}, F1: {f1_scores[c]:.4f}")

        print("Single image prediction complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate UNet semantic segmentation model')
    parser.add_argument('--model_path', type=str, default='logs/best_epoch_weights.h5', help='Model weights path')
    parser.add_argument('--input_shape', type=int, nargs=2, default=[512, 512], help='Input size [height, width]')
    parser.add_argument('--num_classes', type=int, default=3, help='Number of classes (including background)')
    parser.add_argument('--backbone', type=str, default='vgg', choices=['vgg', 'resnet50'], help='Backbone network')
    parser.add_argument('--dataset_path', type=str, default='VOCdevkit', help='Dataset path')
    parser.add_argument('--batch_size', type=int, default=1, help='Batch size')
    parser.add_argument('--miou_out_path', type=str, default='miou_out', help='Evaluation results output path')
    parser.add_argument('--show', action='store_true', help='Display prediction results')
    parser.add_argument('--mode', type=str, default='evaluate', choices=['evaluate', 'predict'],
                        help='evaluate: Evaluate full validation set; predict: Visualize sample images')
    parser.add_argument('--class_names', type=str, nargs='+', default=None,
                        help='Class names (provide one name per class)')

    args = parser.parse_args()

    # Set GPU memory growth
    gpus = tf.config.experimental.list_physical_devices(device_type='GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

    # Run evaluation
    evaluate(
        model_path=args.model_path,
        input_shape=args.input_shape,
        num_classes=args.num_classes,
        backbone=args.backbone,
        dataset_path=args.dataset_path,
        batch_size=args.batch_size,
        miou_out_path=args.miou_out_path,
        show=args.show,
        mode=args.mode,
        class_names=args.class_names
    )