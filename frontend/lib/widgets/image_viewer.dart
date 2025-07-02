import 'package:flutter/material.dart';
import 'package:image_downloader/image_downloader.dart';
import 'package:share_plus/share_plus.dart';

// model thực tế 
class ImageViewer extends StatelessWidget {
  final String imageUrl;      // Link public ảnh trả về từ backend
  final String base64Image;   // Có thể truyền nếu muốn hiển thị nhanh
  final String? shareUrl;     // Nếu có trường riêng cho chia sẻ link

  const ImageViewer({
    Key? key,
    required this.imageUrl,
    required this.base64Image,
    this.shareUrl,
  }) : super(key: key);

  Future<void> _downloadImage(BuildContext context) async {
    try {
      await ImageDownloader.downloadImage(imageUrl);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Đã tải ảnh vào thư viện!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Tải ảnh thất bại!')),
      );
    }
  }

  void _shareImage(BuildContext context) {
    // Nếu muốn chỉ share link, dùng imageUrl hoặc shareUrl
    Share.share(shareUrl ?? imageUrl, subject: "Xem ảnh AI này nè!");
  }

  @override
  Widget build(BuildContext context) {
    // Hiển thị ảnh bằng link public luôn cho tối ưu bộ nhớ
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Hiển thị ảnh từ link public
        Image.network(
          imageUrl,
          fit: BoxFit.contain,
          errorBuilder: (context, error, stackTrace) {
            return Text('Không tải được ảnh!');
          },
        ),
        const SizedBox(height: 20),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton.icon(
              onPressed: () => _downloadImage(context),
              icon: Icon(Icons.download),
              label: Text('Tải về'),
            ),
            const SizedBox(width: 16),
            ElevatedButton.icon(
              onPressed: () => _shareImage(context),
              icon: Icon(Icons.share),
              label: Text('Chia sẻ'),
            ),
          ],
        ),
      ],
    );
  }
}
