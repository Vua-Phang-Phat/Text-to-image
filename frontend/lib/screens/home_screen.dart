import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_gallery_saver/image_gallery_saver.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../models/image_response.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  TextEditingController promptController = TextEditingController();
  ImageResponse? imageResponse;
  bool isLoading = false;

  // Danh sách style và mapping sang tiếng Anh
  final Map<String, String> stylePrompt = {
    'Default': '',
    'Anime': 'in anime style',
    'Oil Painting': 'in oil painting style',
    'Photorealistic': 'photorealistic',
    'Cyberpunk': 'in cyberpunk style',
    'Watercolor': 'in watercolor painting style',
    '3D Render': '3D render',
    'Pixel Art': 'pixel art style',
    'Cartoon': 'cartoon style',
    'Futuristic': 'futuristic style',
  };
  String? selectedStyle; // Chưa chọn thì null, khi chọn sẽ là key

  Future<void> handleGenerate() async {
    setState(() => isLoading = true);
    try {
      String prompt = promptController.text.trim();
      if (selectedStyle != null && selectedStyle != 'Default') {
        String styleStr = stylePrompt[selectedStyle] ?? '';
        if (styleStr.isNotEmpty) {
          prompt += ' $styleStr';
        }
      }
      final result = await ApiService.generateImage(
        prompt,
        512,
        512,
      );
      setState(() {
        imageResponse = result;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => isLoading = false);
    }
  }

  Future<void> handleDownload() async {
    if (imageResponse == null) return;

    // Xin quyền lưu ảnh
    var status = await Permission.storage.request();
    if (!status.isGranted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Không được cấp quyền lưu ảnh!')),
      );
      return;
    }

    Uint8List imageBytes = base64Decode(imageResponse!.imageBase64);
    final result = await ImageGallerySaver.saveImage(
      imageBytes,
      name: "image_ai_${DateTime.now().millisecondsSinceEpoch}",
    );
    if (result['isSuccess'] == true) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã lưu vào thư viện ảnh!')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lưu ảnh thất bại!')),
      );
    }
  }

  Future<void> handleShare() async {
    if (imageResponse == null) return;
    final shareLink = await ApiService.getShareLink(imageResponse!.shareUrl);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Link chia sẻ'),
        content: SelectableText(shareLink),
        actions: [
          TextButton(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: shareLink));
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Đã copy link chia sẻ!')),
              );
            },
            child: const Text('Copy Link'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Đóng'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    Uint8List? imageBytes;
    if (imageResponse != null && imageResponse!.imageBase64.isNotEmpty) {
      imageBytes = base64Decode(imageResponse!.imageBase64);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('AI Art Generator')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: promptController,
              decoration: const InputDecoration(labelText: "Prompt"),
            ),
            const SizedBox(height: 10),

            // Option - chọn style
            Row(
              children: [
                const Text(
                  "Option:",
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButton<String>(
                    value: selectedStyle,
                    hint: const Text("Select style"),
                    isExpanded: true,
                    onChanged: (value) {
                      setState(() {
                        selectedStyle = value;
                      });
                    },
                    items: stylePrompt.keys.map((style) {
                      return DropdownMenuItem(
                        value: style,
                        child: Text(style),
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 10),

            ElevatedButton(
              onPressed: isLoading ? null : handleGenerate,
              child: Text(isLoading ? "Generating..." : "Generate Image"),
            ),
            if (imageBytes != null) ...[
              const SizedBox(height: 16),
              Image.memory(imageBytes, width: 300, height: 300),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    icon: const Icon(Icons.download),
                    tooltip: "Save to gallery",
                    onPressed: handleDownload,
                  ),
                  IconButton(
                    icon: const Icon(Icons.share),
                    tooltip: "Share image link",
                    onPressed: () => handleShare(),
                  ),
                ],
              )
            ]
          ],
        ),
      ),
    );
  }
}
