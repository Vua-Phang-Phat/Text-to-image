import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/image_viewer.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _promptController = TextEditingController();
  String? imageBase64;
  bool isLoading = false;

  // Danh sách các style nghệ thuật
  final List<String> styles = [
    'Realistic',
    'Cartoon',
    'Anime',
    'Oil Painting',
    'Watercolor',
    'Pixel Art',
    'Cyberpunk',
    'Minimalist',
    '3D render',
    'Surrealism',
    'Abstract',
    'Fantasy',
    'Portrait',
    'Landscape',
  ];
  String _selectedStyle = 'Realistic';

  String stylePrompt(String basePrompt, String style) {
    if (style == 'Realistic') return basePrompt;
    return '$basePrompt, in $style style';
  }

  Future<void> _generateImage() async {
    setState(() {
      isLoading = true;
      imageBase64 = null;
    });
    try {
      final promptToSend = stylePrompt(_promptController.text, _selectedStyle);
      final img = await ApiService.generateImage(promptToSend, 1024, 1024);
      setState(() => imageBase64 = img.imageBase64);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lỗi: $e')));
    }
    setState(() {
      isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Text2Image')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _promptController,
              decoration: const InputDecoration(
                labelText: 'Nhập prompt (Anh/Việt/Song ngữ)',
              ),
            ),
            const SizedBox(height: 16),
            // Dropdown chọn style
            DropdownButton<String>(
              value: _selectedStyle,
              isExpanded: true,
              items: styles
                  .map((s) => DropdownMenuItem(
                        value: s,
                        child: Text(s),
                      ))
                  .toList(),
              onChanged: (value) {
                setState(() {
                  _selectedStyle = value!;
                });
              },
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: isLoading ? null : _generateImage,
              child: isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Sinh ảnh'),
            ),
            const SizedBox(height: 24),
            if (imageBase64 != null) ImageViewer(imageBase64: imageBase64!),
          ],
        ),
      ),
    );
  }
}
