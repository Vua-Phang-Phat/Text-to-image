import 'package:flutter/material.dart';
import '../models/image_result.dart';
import '../widgets/image_display.dart';

class ResultScreen extends StatelessWidget {
  final ImageResult imageResult;

  const ResultScreen({Key? key, required this.imageResult}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Kết quả ảnh')),
      body: Center(child: ImageDisplay(imageResult: imageResult)),
    );
  }
}