import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:dio/dio.dart';
import 'package:image_gallery_saver/image_gallery_saver.dart';

class ImageViewer extends StatelessWidget {
  final String imageUrl; // Link ảnh public từ backend (download_url)
  final String? shareUrl;

  const ImageViewer({
    Key? key,
    required this.imageUrl,
    this.shareUrl,
  }) : super(key: key);

  Future<void> _downloadAndSaveImage(BuildContext context, String url) async {
    try {
      // Tải ảnh về bằng dio
      var response = await Dio().get(
        url,
        options: Options(responseType: ResponseType.bytes),
      );
      Uint8List imageBytes = Uint8List.fromList(response.data);

      // Lưu ảnh vào gallery
      final result = await ImageGallerySaver.saveImage(
        imageBytes,
        quality: 80,
        name: "ai_image_${DateTime.now().millisecondsSinceEpoch}",
      );
      if ((result['isSuccess'] ?? false) || (result['filePath'] != null)) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã lưu ảnh vào thư viện!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Lưu ảnh thất bại!')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Lỗi tải ảnh: $e')),
      );
    }
  }

  void _shareImage(BuildContext context, String url) {
    Share.share(url, subject: "Chia sẻ ảnh AI Art");
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (imageUrl.isNotEmpty)
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Image.network(
              imageUrl,
              fit: BoxFit.contain,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return const Center(child: CircularProgressIndicator());
              },
              errorBuilder: (context, error, stackTrace) =>
                  const Icon(Icons.error, size: 60, color: Colors.red),
            ),
          ),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton.icon(
              icon: const Icon(Icons.download),
              label: const Text("Tải về"),
              onPressed: () => _downloadAndSaveImage(context, imageUrl),
            ),
            const SizedBox(width: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.share),
              label: const Text("Chia sẻ"),
              onPressed: () => _shareImage(context, shareUrl ?? imageUrl),
            ),
          ],
        ),
      ],
    );
  }
}
