import 'package:flutter/material.dart';

class PromptInput extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback? onSubmitted;

  const PromptInput({
    Key? key,
    required this.controller,
    this.onSubmitted,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      decoration: const InputDecoration(
        labelText: 'Nhập mô tả ảnh (prompt)',
        border: OutlineInputBorder(),
        prefixIcon: Icon(Icons.edit),
      ),
      minLines: 1,
      maxLines: 3,
      textInputAction: TextInputAction.done,
      onSubmitted: (_) {
        if (onSubmitted != null) onSubmitted!();
      },
    );
  }
}
