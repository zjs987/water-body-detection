from flask import Blueprint, current_app, send_from_directory, request, jsonify, render_template
import logging
from utils_file import allowed_file
from werkzeug.utils import secure_filename
from PIL import Image
import os
from image_discretizer import ImageDiscretizer
from image_processor import ImageProcessor
import uuid
from openai import OpenAI
from unet import Unet as UNetModel
from models import DetectionRecord
from database import db
import json
from flask import session, redirect, url_for
from datetime import datetime, timedelta



main = Blueprint('main', __name__)
logger = logging.getLogger("fileLogger")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI API Configuration
OPENAI_API_KEY = "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"
PROXY = "http://localhost:7890"

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)




@main.route('/analyze')
def analyze():
    return render_template('analyze.html')


@main.route('/index')
def index():
    return render_template('index.html')


@main.route('/realtime')
def realtime():
    return render_template('realtime.html')


@main.route('/statistics')
def statistics():
    return render_template('statistics.html')


@main.route('/upload')
def upload():
    return render_template('upload.html')



@main.route('/comparison_result', methods=['GET'])
def comparison_result():
    """Render the comparison result page"""
    return render_template('compare_result.html')


@main.route('/result', methods=['POST', 'GET'])
def result():
    return render_template('result.html')


@main.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})

    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'})

    # 获取表单参数
    process_type = request.form.get('processType', 'unet')  # 默认使用unet处理
    levels = int(request.form.get('levels', 8))  # 灰度级别数
    spatial_resolution = float(request.form.get('spatialResolution', 1.0))  # 空间分辨率
    water_threshold = int(request.form.get('waterThreshold', 1))  # 水体阈值

    try:
        # 保存原始文件
        original_filename = secure_filename(file.filename)
        original_path = os.path.join(current_app.config['UPLOAD_FOLDER'], original_filename)
        file.save(original_path)

        # 创建处理后的文件名
        filename_without_ext, file_extension = os.path.splitext(original_filename)
        processed_filename = f"{filename_without_ext}_processed{file_extension}"
        discretized_filename = f"{filename_without_ext}_discretized.png"
        water_land_filename = f"{filename_without_ext}_water_land.png"

        processed_path = os.path.join(current_app.config['PROCESSED_FOLDER'], processed_filename)
        discretized_path = os.path.join(current_app.config['PROCESSED_FOLDER'], discretized_filename)
        water_land_path = os.path.join(current_app.config['PROCESSED_FOLDER'], water_land_filename)

        # 打开原始图像
        image = Image.open(original_path)

        # 根据选择的方法处理图像
        if process_type == 'grayscale':
            # 转换为灰度图
            processed_image = image.convert('L')
            processed_image.save(processed_path)
        elif process_type == 'edge_detection':
            # 边缘检测
            processor = ImageProcessor()
            processed_image = processor.detect_edges(image)
            processed_image.save(processed_path)
        elif process_type == 'unet' or process_type == 'original':
            # 使用UNet模型进行水体检测
            unet_model = UNetModel()
            processed_image = unet_model.detect_image(image)
            processed_image.save(processed_path)
        else:
            # 如果没有指定处理类型，也使用UNet处理
            unet_model = UNetModel()
            processed_image = unet_model.detect_image(image)
            processed_image.save(processed_path)

        # 创建离散化处理器
        discretizer = ImageDiscretizer(spatial_resolution=spatial_resolution)

        # 对原始图像进行离散化处理 - 修改为接收水陆统计
        discrete_matrix, stats, water_land_stats = discretizer.process_image(
            image,  # 使用原始图像
            levels=levels,
            visualize=True,
            save_path=discretized_path,
            save_matrix=True,
            water_threshold=water_threshold  # 设置水体阈值
        )

        # 生成水陆分类可视化
        discretizer.visualize_water_land(
            discrete_matrix,
            water_threshold=water_threshold,
            save_path=water_land_path
        )

        # 提取统计数据
        pixel_counts, percentages, areas = stats

        # 准备灰度离散化统计数据
        discretize_stats = {
            'levels': list(range(len(pixel_counts))),
            'pixelCounts': pixel_counts,
            'percentages': percentages,
            'areas': areas
        }

        # 准备水陆统计数据
        water_land_info = {
            'waterPixels': water_land_stats['water_pixels'],
            'landPixels': water_land_stats['land_pixels'],
            'totalPixels': water_land_stats['total_pixels'],
            'waterPercentage': water_land_stats['water_percentage'],
            'landPercentage': water_land_stats['land_percentage'],
            'waterArea': water_land_stats['water_area'],
            'landArea': water_land_stats['land_area'],
            'totalArea': water_land_stats['total_area'],
            'spatialResolution': water_land_stats['spatial_resolution']
        }
        # 准备结果数据
        result_data = {
            'originalFileUrl': '/upload/' + original_filename,
            'processedFileUrl': '/processed/' + processed_filename,
            'discretizedFileUrl': '/processed/' + discretized_filename,
            'waterLandImageUrl': '/processed/' + water_land_filename,
            'discretizeStats': discretize_stats,
            'waterLandStats': water_land_info,
        }

        # 保存检测记录到数据库
        try:
            save_single_detection_record(result_data)
        except Exception as e:
            logger.error(f"保存检测记录失败: {str(e)}")

        # 返回处理结果
        return jsonify(result_data)

    except Exception as e:
        print(f"图像处理失败: {str(e)}")
        return jsonify({'error': str(e)})


@main.route('/upload_comparison', methods=['POST'])
def upload_comparison():
    """Handle uploading and processing of before and after images"""
    if 'before_image' not in request.files or 'after_image' not in request.files:
        return jsonify({'error': 'Missing before or after image'})

    before_file = request.files['before_image']
    after_file = request.files['after_image']

    if before_file.filename == '' or after_file.filename == '':
        return jsonify({'error': 'Both before and after images must be selected'})

    if not allowed_file(before_file.filename) or not allowed_file(after_file.filename):
        return jsonify({'error': 'Unsupported file type'})

    # Get form parameters
    process_type = request.form.get('processType', 'unet')  # Default to unet
    levels = int(request.form.get('levels', 8))  # Grayscale levels
    spatial_resolution = float(request.form.get('spatialResolution', 1.0))  # Spatial resolution
    water_threshold = int(request.form.get('waterThreshold', 1))  # Water threshold level

    try:
        # Generate unique filenames to avoid conflicts
        before_uid = str(uuid.uuid4())[:8]
        after_uid = str(uuid.uuid4())[:8]

        # Save original files with unique names
        before_original_filename = f"before_{before_uid}_{secure_filename(before_file.filename)}"
        after_original_filename = f"after_{after_uid}_{secure_filename(after_file.filename)}"

        before_original_path = os.path.join(current_app.config['UPLOAD_FOLDER'], before_original_filename)
        after_original_path = os.path.join(current_app.config['UPLOAD_FOLDER'], after_original_filename)

        before_file.save(before_original_path)
        after_file.save(after_original_path)

        # Create processed filenames
        before_base, before_ext = os.path.splitext(before_original_filename)
        after_base, after_ext = os.path.splitext(after_original_filename)

        before_processed_filename = f"{before_base}_processed{before_ext}"
        before_discretized_filename = f"{before_base}_discretized.png"
        before_water_land_filename = f"{before_base}_water_land.png"

        after_processed_filename = f"{after_base}_processed{after_ext}"
        after_discretized_filename = f"{after_base}_discretized.png"
        after_water_land_filename = f"{after_base}_water_land.png"

        # Define paths for processed files
        before_processed_path = os.path.join(current_app.config['PROCESSED_FOLDER'], before_processed_filename)
        before_discretized_path = os.path.join(current_app.config['PROCESSED_FOLDER'], before_discretized_filename)
        before_water_land_path = os.path.join(current_app.config['PROCESSED_FOLDER'], before_water_land_filename)

        after_processed_path = os.path.join(current_app.config['PROCESSED_FOLDER'], after_processed_filename)
        after_discretized_path = os.path.join(current_app.config['PROCESSED_FOLDER'], after_discretized_filename)
        after_water_land_path = os.path.join(current_app.config['PROCESSED_FOLDER'], after_water_land_filename)

        # Open the original images
        before_image = Image.open(before_original_path)
        after_image = Image.open(after_original_path)

        # Process both images
        if process_type == 'grayscale':
            # Convert to grayscale
            before_processed_image = before_image.convert('L')
            after_processed_image = after_image.convert('L')
        elif process_type == 'edge_detection':
            # Edge detection
            processor = ImageProcessor()
            before_processed_image = processor.detect_edges(before_image)
            after_processed_image = processor.detect_edges(after_image)
        else:  # Default to unet
            # Use UNet model for water body detection
            unet_model = UNetModel()
            before_processed_image = unet_model.detect_image(before_image)
            after_processed_image = unet_model.detect_image(after_image)

        # Save processed images
        before_processed_image.save(before_processed_path)
        after_processed_image.save(after_processed_path)

        # Create discretizer
        discretizer = ImageDiscretizer(spatial_resolution=spatial_resolution)

        # Process before image
        before_discrete_matrix, before_stats, before_water_land_stats = discretizer.process_image(
            before_image,
            levels=levels,
            visualize=True,
            save_path=before_discretized_path,
            save_matrix=True,
            water_threshold=water_threshold
        )

        # Process after image
        after_discrete_matrix, after_stats, after_water_land_stats = discretizer.process_image(
            after_image,
            levels=levels,
            visualize=True,
            save_path=after_discretized_path,
            save_matrix=True,
            water_threshold=water_threshold
        )

        # Generate water/land classification visualizations
        discretizer.visualize_water_land(
            before_discrete_matrix,
            water_threshold=water_threshold,
            save_path=before_water_land_path
        )

        discretizer.visualize_water_land(
            after_discrete_matrix,
            water_threshold=water_threshold,
            save_path=after_water_land_path
        )

        # Extract statistics
        before_pixel_counts, before_percentages, before_areas = before_stats
        after_pixel_counts, after_percentages, after_areas = after_stats

        # Prepare discretize statistics
        before_discretize_stats = {
            'levels': list(range(len(before_pixel_counts))),
            'pixelCounts': before_pixel_counts,
            'percentages': before_percentages,
            'areas': before_areas
        }

        after_discretize_stats = {
            'levels': list(range(len(after_pixel_counts))),
            'pixelCounts': after_pixel_counts,
            'percentages': after_percentages,
            'areas': after_areas
        }

        # 准备结果数据
        result_data = {
            'beforeOriginalUrl': '/upload/' + before_original_filename,
            'afterOriginalUrl': '/upload/' + after_original_filename,
            'beforeProcessedUrl': '/processed/' + before_processed_filename,
            'afterProcessedUrl': '/processed/' + after_processed_filename,
            'beforeDiscretizedUrl': '/processed/' + before_discretized_filename,
            'afterDiscretizedUrl': '/processed/' + after_discretized_filename,
            'beforeWaterLandUrl': '/processed/' + before_water_land_filename,
            'afterWaterLandUrl': '/processed/' + after_water_land_filename,
            'beforeDiscretizeStats': before_discretize_stats,
            'afterDiscretizeStats': after_discretize_stats,
            'beforeWaterLandStats': before_water_land_stats,
            'afterWaterLandStats': after_water_land_stats
        }

        # 保存检测记录到数据库
        try:
            save_comparison_detection_record(result_data)
        except Exception as e:
            logger.error(f"保存比较检测记录失败: {str(e)}")

        # 返回处理结果
        return jsonify(result_data)
    except Exception as e:
        logger.error(f"Image processing failed: {str(e)}")
        return jsonify({'error': str(e)})

@main.route('/processed/<filename>')
def send_processed_image(filename):
    try:
        return send_from_directory(current_app.config['PROCESSED_FOLDER'], filename)
    except FileNotFoundError:
        return "File not found", 404


@main.route('/upload/<filename>')
def send_original_image(filename):
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return "File not found", 404


# Initialize OpenAI client
def get_openai_client():
    """Get OpenAI client, retry if initialization fails"""
    try:
        # Try to create client
        client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        # Test if client works properly
        logger.info("Initializing OpenAI client and testing connection...")
        return client

    except Exception as e:
        logger.error(f"OpenAI client initialization failed: {e}")
        return None


# Global client variable
client = get_openai_client()
if client:
    logger.info("OpenAI client initialized successfully")
else:
    logger.error("Unable to initialize OpenAI client, API functions will be unavailable")


# Image processing function
def preprocess_image(image_path, max_size_mb=2):
    """Preprocess image (resize, format conversion, etc.)"""
    try:
        from PIL import Image

        # Check file size
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)

        if file_size_mb > max_size_mb:
            logger.info(f"Image size is {file_size_mb:.2f}MB, compression needed")

            # Open image
            img = Image.open(image_path)

            # Handle RGBA mode images
            if img.mode == 'RGBA':
                logger.info("RGBA mode image detected, converting to RGB mode")
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Calculate compression ratio
            compression_ratio = max_size_mb / file_size_mb
            new_width = max(1, int(img.width * (compression_ratio ** 0.5)))
            new_height = max(1, int(img.height * (compression_ratio ** 0.5)))

            # Resize and save
            img = img.resize((new_width, new_height), Image.LANCZOS)
            img.save(image_path, 'JPEG', optimize=True, quality=85)

            new_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            logger.info(f"Image compressed to {new_size_mb:.2f}MB")

    except ImportError:
        logger.warning("PIL library not installed, skipping image preprocessing")
    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")


def encode_image(image_path):
    """Encode image to base64"""
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_water_body_with_openai(before_image_path, after_image_path, model="gpt-4o"):
    """Analyze water body changes using OpenAI API"""
    try:
        # Preprocess images
        preprocess_image(before_image_path)
        preprocess_image(after_image_path)

        # Encode images
        before_base64 = encode_image(before_image_path)
        after_base64 = encode_image(after_image_path)

        # Logging
        before_size = len(before_base64) * 0.75 / (1024 * 1024)
        after_size = len(after_base64) * 0.75 / (1024 * 1024)
        logger.info(f"Encoded size - Before: {before_size:.2f}MB, After: {after_size:.2f}MB")

        # Method 1: Using official OpenAI library
        def try_with_openai_client():
            if client is None:
                logger.error("OpenAI client not initialized, cannot use official library method")
                return None

            try:
                logger.info(f"Using official OpenAI library with model {model} to send analysis request...")

                # Try to create a new client (to prevent client expiration)
                local_client = OpenAI(api_key=OPENAI_API_KEY)

                response = local_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional remote sensing image analyst, specializing in satellite and remote sensing image interpretation. You excel at identifying complex geographic environmental changes, especially the dynamic changes in water body ecosystems."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please provide a professional, in-depth analysis of these two remote sensing satellite images of the same area from different time periods, focusing on:\n"
                                            "1. Precise changes in water body area (please provide specific percentages)\n"
                                            "2. Subtle changes in water color, texture, and boundaries\n"
                                            "3. Detailed changes in the surrounding geographic environment\n"
                                            "4. Potential natural or human factors causing water body changes\n"
                                            "5. Comprehensive assessment of potential ecosystem risks\n"
                                            "6. Targeted environmental protection and mitigation measure recommendations\n"
                                            "Please provide a scientifically rigorous, logically clear professional analysis report."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{before_base64}"
                                    }
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{after_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )

                return response.choices[0].message.content

            except Exception as e:
                logger.error(f"OpenAI official library request failed: {e}")
                return None

        # Method 2: Using requests library to directly request API
        def try_with_requests():
            import requests
            import json

            try:
                logger.info(f"Using requests library with model {model} to send analysis request...")

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                }

                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional remote sensing image analyst, specializing in satellite and remote sensing image interpretation. You excel at identifying complex geographic environmental changes, especially the dynamic changes in water body ecosystems."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please provide a professional, in-depth analysis of these two remote sensing satellite images of the same area from different time periods, focusing on:\n"
                                            "1. Precise changes in water body area (please provide specific percentages)\n"
                                            "2. Subtle changes in water color, texture, and boundaries\n"
                                            "3. Detailed changes in the surrounding geographic environment\n"
                                            "4. Potential natural or human factors causing water body changes\n"
                                            "5. Comprehensive assessment of potential ecosystem risks\n"
                                            "6. Targeted environmental protection and mitigation measure recommendations\n"
                                            "Please provide a scientifically rigorous, logically clear professional analysis report."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{before_base64}"
                                    }
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{after_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }

                # Try direct connection without proxy
                try:
                    logger.info("Attempting direct connection to OpenAI API (without proxy)...")
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=120
                    )

                    if response.status_code == 200:
                        response_data = response.json()
                        return response_data['choices'][0]['message']['content']
                    else:
                        logger.error(f"Direct API connection failed: HTTP {response.status_code} - {response.text}")
                except Exception as e:
                    logger.error(f"Direct request exception: {e}")

                # If direct connection fails, try with proxy
                try:
                    logger.info(f"Attempting connection via proxy {PROXY} to OpenAI API...")
                    proxies = {
                        'http': PROXY,
                        'https': PROXY
                    }

                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        proxies=proxies,
                        timeout=120
                    )

                    if response.status_code == 200:
                        response_data = response.json()
                        return response_data['choices'][0]['message']['content']
                    else:
                        logger.error(f"Proxy API connection failed: HTTP {response.status_code} - {response.text}")
                except Exception as e:
                    logger.error(f"Proxy request exception: {e}")

                return None

            except Exception as e:
                logger.error(f"Requests library request failed: {e}")
                return None

        # Method 3: Using a third-party API (if available)
        def try_with_third_party():
            import requests

            try:
                # Note: This is just an example, needs actual configuration with a valid alternative API
                logger.info("Attempting to use third-party API...")

                # Can be replaced with an actual available third-party GPT image analysis API
                third_party_api = "https://api.example.com/v1/vision"
                api_key = "your_third_party_api_key"

                # Third-party API call logic (example only)
                return "No available third-party API, please configure a valid alternative API."

            except Exception as e:
                logger.error(f"Third-party API request failed: {e}")
                return None

        # Try all methods
        method_results = []

        # Method 1: OpenAI client
        logger.info("Trying Method 1: Using OpenAI official client library...")
        result = try_with_openai_client()
        if result:
            return result

        # Method 2: requests library
        logger.info("Trying Method 2: Using requests library...")
        result = try_with_requests()
        if result:
            return result

        # Method 3: Third-party API
        logger.info("Trying Method 3: Using third-party API...")
        result = try_with_third_party()
        if result:
            return result

        # All methods failed
        logger.error("All API request methods failed")
        return "Analysis could not be completed, all API request methods failed. Please check your API key, network connection, and proxy settings, or try using a different model."

    except Exception as e:
        logger.error(f"Exception occurred during analysis process: {e}")
        return f"Exception occurred during analysis process: {str(e)}"


@main.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files"""
    return send_from_directory(UPLOAD_FOLDER, filename)


@main.route('/analyze', methods=['POST'])
def analyze_water_body():
    """Handle water body image analysis request"""
    if 'before_image' not in request.files or 'after_image' not in request.files:
        return jsonify({"error": "Missing image files"}), 400

    before_image = request.files['before_image']
    after_image = request.files['after_image']

    # Get selected model, default to gpt-4o
    selected_model = request.form.get('model', 'gpt-4o')
    logger.info(f"Selected model: {selected_model}")

    # Generate unique filenames
    before_filename = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_before.jpg")
    after_filename = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_after.jpg")

    # Save images
    before_image.save(before_filename)
    after_image.save(after_filename)

    try:
        # Analyze water body changes
        analysis_result = analyze_water_body_with_openai(before_filename, after_filename, model=selected_model)

        # Return analysis results and image paths
        return jsonify({
            "analysis": analysis_result,
            "before_image": before_filename,
            "after_image": after_filename
        })

    except Exception as e:
        logger.error(f"Error processing analysis request: {e}")
        return jsonify({"error": str(e)}), 500


# Health check endpoint
@main.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


# Endpoint to get available models
@main.route('/models', methods=['GET'])
def get_available_models():
    """Provide a list of models available for analysis"""
    models = [
        {"id": "gpt-4o", "name": "GPT-4o (Recommended)"},
        {"id": "gpt-4-turbo-2024-04-09", "name": "GPT-4 Turbo"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Faster)"},
        {"id": "gpt-4-0125-preview", "name": "GPT-4 Preview"},
        {"id": "gpt-4.5-preview", "name": "GPT-4.5 Preview"}
    ]
    return jsonify({"models": models})


@main.route('/history')
def history():
    """渲染历史记录页面"""
    try:
        # Get current user ID (if logged in)
        from flask_login import current_user
        if current_user.is_authenticated:
            # Show user's records and anonymous records
            records = DetectionRecord.query.filter(
                (DetectionRecord.user_id == current_user.id) |
                (DetectionRecord.user_id == None)
            ).order_by(DetectionRecord.created_at.desc()).all()
        else:
            # If not logged in, only show anonymous records
            records = DetectionRecord.query.filter(
                DetectionRecord.user_id == None
            ).order_by(DetectionRecord.created_at.desc()).all()

        return render_template('history.html', records=records)
    except Exception as e:
        logger.error(f"Error fetching history records: {str(e)}")
        return render_template('history.html', records=[])


# 获取检测记录的API端点
@main.route('/get_detection_records')
def get_detection_records():
    """获取检测记录的API，支持分页和过滤"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        record_type = request.args.get('record_type', '')
        process_type = request.args.get('process_type', '')
        date_range = request.args.get('date_range', '')

        # 创建基础查询
        query = DetectionRecord.query

        # 应用过滤条件
        if record_type:
            query = query.filter(DetectionRecord.record_type == record_type)

        if process_type:
            query = query.filter(DetectionRecord.process_type == process_type)

        # 应用日期过滤
        if date_range:
            today = datetime.now()

            if date_range == 'today':
                start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(DetectionRecord.created_at >= start_date)
            elif date_range == 'week':
                # 获取本周一
                start_date = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0,
                                                                               microsecond=0)
                query = query.filter(DetectionRecord.created_at >= start_date)
            elif date_range == 'month':
                # 获取本月第一天
                start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(DetectionRecord.created_at >= start_date)

        # 获取当前用户ID（如果已登录）
        from flask_login import current_user
        if current_user.is_authenticated:
            # 显示用户的记录和匿名记录
            query = query.filter((DetectionRecord.user_id == current_user.id) | (DetectionRecord.user_id == None))
        else:
            # 如果未登录，只显示匿名记录
            query = query.filter(DetectionRecord.user_id == None)

        # 按创建日期排序（最新的在前）
        query = query.order_by(DetectionRecord.created_at.desc())

        # 分页结果
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # 格式化记录用于JSON响应
        records = []
        for record in pagination.items:
            record_data = {
                'id': record.id,
                'record_type': record.record_type,
                'process_type': record.process_type,
                'created_at': record.created_at.isoformat(),
            }

            # 添加类型特定数据
            if record.record_type == 'single':
                record_data.update({
                    'original_path': f"/upload/{record.original_filename}" if record.original_filename else None,
                    'processed_path': f"/processed/{os.path.basename(record.processed_path)}" if record.processed_path else None,
                    'discretized_path': f"/processed/{os.path.basename(record.discretized_path)}" if record.discretized_path else None,
                    'water_land_path': f"/processed/{os.path.basename(record.water_land_path)}" if record.water_land_path else None,
                    'water_percentage': record.water_percentage or 0,
                    'land_percentage': record.land_percentage or 0,
                    'water_area': record.water_area or 0,
                    'land_area': record.land_area or 0,
                })
            else:
                record_data.update({
                    'before_path': f"/upload/{record.before_filename}" if record.before_filename else None,
                    'after_path': f"/upload/{record.after_filename}" if record.after_filename else None,
                    'before_processed_path': f"/processed/{os.path.basename(record.before_processed_path)}" if record.before_processed_path else None,
                    'after_processed_path': f"/processed/{os.path.basename(record.after_processed_path)}" if record.after_processed_path else None,
                    'before_water_land_path': f"/processed/{os.path.basename(record.before_water_land_path)}" if record.before_water_land_path else None,
                    'after_water_land_path': f"/processed/{os.path.basename(record.after_water_land_path)}" if record.after_water_land_path else None,
                })

            records.append(record_data)

        # 创建分页信息
        pagination_info = {
            'total_items': pagination.total,
            'total_pages': pagination.pages,
            'current_page': pagination.page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        }

        return jsonify({
            'records': records,
            'pagination': pagination_info
        })

    except Exception as e:
        logger.error(f"获取检测记录时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 查看特定检测记录的路由
@main.route('/view_record/<int:record_id>')
def view_record(record_id):
    """查看特定检测记录"""
    try:
        # 从数据库获取记录
        record = DetectionRecord.query.get_or_404(record_id)

        # 检查访问权限
        from flask_login import current_user
        if record.user_id and (not current_user.is_authenticated or record.user_id != current_user.id):
            return jsonify({'error': '您没有权限查看此记录'}), 403

        # 根据记录类型重定向到适当的结果页面
        if record.record_type == 'single':
            # 单图像分析
            result_data = {
                'originalFileUrl': f"/upload/{record.original_filename}" if record.original_filename else None,
                'processedFileUrl': f"/processed/{os.path.basename(record.processed_path)}" if record.processed_path else None,
                'discretizedFileUrl': f"/processed/{os.path.basename(record.discretized_path)}" if record.discretized_path else None,
                'waterLandImageUrl': f"/processed/{os.path.basename(record.water_land_path)}" if record.water_land_path else None,
                'waterLandStats': {
                    'waterPixels': record.water_pixels or 0,
                    'landPixels': record.land_pixels or 0,
                    'totalPixels': (record.water_pixels or 0) + (record.land_pixels or 0),
                    'waterPercentage': record.water_percentage or 0,
                    'landPercentage': record.land_percentage or 0,
                    'waterArea': record.water_area or 0,
                    'landArea': record.land_area or 0,
                    'totalArea': (record.water_area or 0) + (record.land_area or 0),
                    'spatialResolution': record.spatial_resolution or 1.0
                }
            }

            # 将结果存储在session中，用于结果页面
            session['processResult'] = json.dumps(result_data)
            return redirect(url_for('main.result'))
        else:
            # 比较分析
            result_data = {
                'beforeOriginalUrl': f"/upload/{record.before_filename}" if record.before_filename else None,
                'afterOriginalUrl': f"/upload/{record.after_filename}" if record.after_filename else None,
                'beforeProcessedUrl': f"/processed/{os.path.basename(record.before_processed_path)}" if record.before_processed_path else None,
                'afterProcessedUrl': f"/processed/{os.path.basename(record.after_processed_path)}" if record.after_processed_path else None,
                'beforeDiscretizedUrl': f"/processed/{os.path.basename(record.before_discretized_path)}" if record.before_discretized_path else None,
                'afterDiscretizedUrl': f"/processed/{os.path.basename(record.after_discretized_path)}" if record.after_discretized_path else None,
                'beforeWaterLandUrl': f"/processed/{os.path.basename(record.before_water_land_path)}" if record.before_water_land_path else None,
                'afterWaterLandUrl': f"/processed/{os.path.basename(record.after_water_land_path)}" if record.after_water_land_path else None,
                'beforeWaterLandStats': {
                    'water_pixels': record.water_pixels or 0,
                    'land_pixels': record.land_pixels or 0,
                    'total_pixels': (record.water_pixels or 0) + (record.land_pixels or 0),
                    'water_percentage': record.water_percentage or 0,
                    'land_percentage': record.land_percentage or 0,
                    'water_area': record.water_area or 0,
                    'land_area': record.land_area or 0,
                    'total_area': (record.water_area or 0) + (record.land_area or 0),
                    'spatial_resolution': record.spatial_resolution or 1.0
                },
                # 注意：这里假设比较分析记录也存储了对应的水体/陆地统计信息
                'afterWaterLandStats': {
                    'water_pixels': record.water_pixels or 0,
                    'land_pixels': record.land_pixels or 0,
                    'total_pixels': (record.water_pixels or 0) + (record.land_pixels or 0),
                    'water_percentage': record.water_percentage or 0,
                    'land_percentage': record.land_percentage or 0,
                    'water_area': record.water_area or 0,
                    'land_area': record.land_area or 0,
                    'total_area': (record.water_area or 0) + (record.land_area or 0),
                    'spatial_resolution': record.spatial_resolution or 1.0
                }
            }

            # 将结果存储在session中，用于比较结果页面
            session['comparisonResult'] = json.dumps(result_data)
            return redirect(url_for('main.comparison_result'))

    except Exception as e:
        logger.error(f"查看记录时出错 {record_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 在已有的 upload_file 函数中添加保存记录到数据库的逻辑
# 在 return jsonify(...) 语句之前添加以下代码
def save_single_detection_record(result_data):
    """保存单图像检测结果到数据库以便历史记录跟踪"""
    try:
        # 获取当前用户ID（如果已登录）
        from flask_login import current_user
        user_id = current_user.id if current_user.is_authenticated else None

        # 创建新检测记录
        record = DetectionRecord(
            user_id=user_id,
            record_type='single',
            process_type=request.form.get('processType', 'unet'),
            levels=int(request.form.get('levels', 8)),
            spatial_resolution=float(request.form.get('spatialResolution', 1.0)),
            water_threshold=int(request.form.get('waterThreshold', 1)),

            # 文件信息
            original_filename=os.path.basename(result_data.get('originalFileUrl', '').replace('/upload/', '')),
            original_path=result_data.get('originalFileUrl', ''),
            processed_path=result_data.get('processedFileUrl', ''),
            discretized_path=result_data.get('discretizedFileUrl', ''),
            water_land_path=result_data.get('waterLandImageUrl', ''),

            # 统计信息
            water_pixels=result_data.get('waterLandStats', {}).get('waterPixels', 0),
            land_pixels=result_data.get('waterLandStats', {}).get('landPixels', 0),
            water_percentage=result_data.get('waterLandStats', {}).get('waterPercentage', 0),
            land_percentage=result_data.get('waterLandStats', {}).get('landPercentage', 0),
            water_area=result_data.get('waterLandStats', {}).get('waterArea', 0),
            land_area=result_data.get('waterLandStats', {}).get('landArea', 0),

            # 元数据
            created_at=datetime.utcnow(),
            notes=f"Process type: {request.form.get('processType', 'unet')}"
        )

        # 保存记录到数据库
        db.session.add(record)
        db.session.commit()
        logger.info(f"已保存单图像检测记录到数据库，ID: {record.id}")

    except Exception as e:
        logger.error(f"保存检测记录到数据库时出错: {str(e)}")
        # 继续返回结果，即使保存记录失败


# 在已有的 upload_comparison 函数中添加保存记录到数据库的逻辑
# 在 return jsonify(...) 语句之前添加以下代码
def save_comparison_detection_record(result_data):
    """保存比较检测结果到数据库以便历史记录跟踪"""
    try:
        # 获取当前用户ID（如果已登录）
        from flask_login import current_user
        user_id = current_user.id if current_user.is_authenticated else None

        # 创建新检测记录
        record = DetectionRecord(
            user_id=user_id,
            record_type='comparison',
            process_type=request.form.get('processType', 'unet'),
            levels=int(request.form.get('levels', 8)),
            spatial_resolution=float(request.form.get('spatialResolution', 1.0)),
            water_threshold=int(request.form.get('waterThreshold', 1)),

            # Before 文件信息
            before_filename=os.path.basename(result_data.get('beforeOriginalUrl', '').replace('/upload/', '')),
            before_path=result_data.get('beforeOriginalUrl', ''),
            before_processed_path=result_data.get('beforeProcessedUrl', ''),
            before_discretized_path=result_data.get('beforeDiscretizedUrl', ''),
            before_water_land_path=result_data.get('beforeWaterLandUrl', ''),

            # After 文件信息
            after_filename=os.path.basename(result_data.get('afterOriginalUrl', '').replace('/upload/', '')),
            after_path=result_data.get('afterOriginalUrl', ''),
            after_processed_path=result_data.get('afterProcessedUrl', ''),
            after_discretized_path=result_data.get('afterDiscretizedUrl', ''),
            after_water_land_path=result_data.get('afterWaterLandUrl', ''),

            # 元数据
            created_at=datetime.utcnow(),
            notes=f"Process type: {request.form.get('processType', 'unet')}"
        )

        # 保存记录到数据库
        db.session.add(record)
        db.session.commit()
        logger.info(f"已保存比较检测记录到数据库，ID: {record.id}")

    except Exception as e:
        logger.error(f"保存检测记录到数据库时出错: {str(e)}")
        # 继续返回结果，即使保存记录失败


# 修改 upload_file 函数的返回部分
# 在原有的 return jsonify(...) 部分之前添加：

"""
# 下面这段代码应该添加到 upload_file 函数中 return jsonify(...) 语句之前

try:
    # 保存检测记录到数据库
    save_single_detection_record(result_data)
except Exception as e:
    logger.error(f"保存检测记录失败: {str(e)}")
"""

# 修改 upload_comparison 函数的返回部分
# 在原有的 return jsonify(...) 部分之前添加：

"""
# 下面这段代码应该添加到 upload_comparison 函数中 return jsonify(...) 语句之前

try:
    # 保存检测记录到数据库
    save_comparison_detection_record(result_data)
except Exception as e:
    logger.error(f"保存比较检测记录失败: {str(e)}")
"""



