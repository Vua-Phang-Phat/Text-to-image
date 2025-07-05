import 'dart:convert';
import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../services/api_service.dart';
import '../models/image_response.dart';



class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _promptController = TextEditingController();
  final TextEditingController _customStyleController = TextEditingController();

  final List<String> _artStyles = [
    '', // Không chọn phong cách (mặc định)
    'Photorealistic (Chân thực)',
    'Anime (Hoạt hình Nhật Bản)',
    'Cyberpunk (Tương lai, neon)',
    'Watercolor (Tranh màu nước)',
    'Oil Painting (Tranh sơn dầu)',
    'Pixel Art (Game pixel)',
    '3D Render (Đồ họa 3D)',
    'Cartoon (Hoạt hình)',
    'Sketch (Phác thảo)',
    'Khác / Tuỳ chọn...', // Cho phép nhập style tự do
  ];
  String? _selectedStyle = ''; // Mặc định là không chọn phong cách
  bool _isLoading = false;
  Uint8List? _imageBytes;

  String buildPrompt(String prompt, String style, String customStyle) {
    if (style == 'Khác / Tuỳ chọn...') {
      return "${prompt.trim()}, ${customStyle.trim()}";
    }
    if (style.trim().isEmpty) return prompt;
    return "$prompt, $style";
  }

  Future<void> _generateImage() async {
    final style = _selectedStyle ?? '';
    final isCustom = style == 'Khác / Tuỳ chọn...';
    final customStyle = _customStyleController.text.trim();

    if (_promptController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hãy nhập mô tả ảnh!')),
      );
      return;
    }

    if (isCustom && customStyle.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Bạn cần nhập phong cách nghệ thuật tuỳ ý!')),
      );
      return;
    }

    final prompt = buildPrompt(
      _promptController.text.trim(),
      style,
      customStyle,
    );
    setState(() {
      _isLoading = true;
      _imageBytes = null;
    });

    try {
      final ImageResponse response = await ApiService.generateImage(prompt, 1024, 1024);
      if (response.imageBase64 == null || response.imageBase64!.isEmpty) {
        throw Exception("Không nhận được ảnh từ backend!");
      }
      setState(() {
        _imageBytes = base64Decode(response.imageBase64!);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      print('Lỗi gọi API: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Lỗi gọi API: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isCustom = _selectedStyle == 'Khác / Tuỳ chọn...';

    return Scaffold(
      appBar: AppBar(
        title: Text('Tạo Ảnh Nghệ Thuật'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _promptController,
              decoration: InputDecoration(
                labelText: 'Nhập mô tả ảnh (prompt)...',
                border: OutlineInputBorder(),
              ),
              minLines: 2,
              maxLines: 4,
            ),
            SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedStyle,
              items: _artStyles.map((style) => DropdownMenuItem(
                value: style,
                child: Text(
                  style.isEmpty
                    ? "Không chọn phong cách (mặc định)"
                    : style,
                ),
              )).toList(),
              decoration: InputDecoration(
                labelText: 'Chọn thể loại nghệ thuật (option)',
                border: OutlineInputBorder(),
              ),
              onChanged: (value) {
                setState(() {
                  _selectedStyle = value;
                  if (_selectedStyle != 'Khác / Tuỳ chọn...') {
                    _customStyleController.clear();
                  }
                });
              },
            ),
            if (isCustom)
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: TextField(
                  controller: _customStyleController,
                  decoration: InputDecoration(
                    labelText: 'Nhập phong cách nghệ thuật tuỳ ý...',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _isLoading ? null : _generateImage,
              child: _isLoading
                  ? SizedBox(width: 20, height: 20, child: CircularProgressIndicator())
                  : Text('Tạo ảnh'),
            ),
            SizedBox(height: 22),
            if (_imageBytes != null)
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Image.memory(
                    _imageBytes!,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}