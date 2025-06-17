import 'dart:typed_data';
import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';

class ImageViewer extends StatelessWidget {
  final String imageBase64;
  const ImageViewer({super.key, required this.imageBase64});

  Future<void> downloadImage(BuildContext context) async {
    try {
      Uint8List bytes = base64Decode(imageBase64);

      // Xin quyền lưu Android
      await Permission.storage.request();

      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/image_${DateTime.now().millisecondsSinceEpoch}.png');
      await file.writeAsBytes(bytes);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Đã lưu ảnh: ${file.path}')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Lỗi khi lưu ảnh: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    Uint8List bytes = base64Decode(imageBase64);
    return SingleChildScrollView(
      child: Column(
        children: [
          SizedBox(
            height: 320, 
            child: Image.memory(
              bytes,
              fit: BoxFit.contain,
            ),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            icon: const Icon(Icons.download),
            label: const Text('Tải về'),
            onPressed: () => downloadImage(context),
          ),
        ],
      ),
    );
  }
}
