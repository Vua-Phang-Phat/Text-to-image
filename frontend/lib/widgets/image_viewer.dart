import 'dart:convert';
import 'package:flutter/material.dart';

class ImageViewer extends StatelessWidget {
  final String imageBase64;

  const ImageViewer({super.key, required this.imageBase64});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ảnh nghệ thuật')),
      body: Center(
        child: Image.memory(base64Decode(imageBase64)),
      ),
    );
  }
}
