import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/image_result.dart';

class ImageDisplay extends StatelessWidget {
  final ImageResult imageResult;

  const ImageDisplay({Key? key, required this.imageResult}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (imageResult.base64 != null) {
      // Ảnh base64
      return Image.memory(base64Decode(imageResult.base64!));
    } else if (imageResult.url != null) {
      // Ảnh từ URL (demo hoặc lỗi)
      return Image.network(imageResult.url!);
    } else {
      return const Text('Không có ảnh để hiển thị.');
    }
  }
}