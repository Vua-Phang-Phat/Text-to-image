import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/image_result.dart';

class ApiService {
  static const String baseUrl = 'https://t2image-394672402684.us-central1.run.app';

  static Future<ImageResult?> generateImage(String prompt) async {
    final url = Uri.parse('$baseUrl/generate-image');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'prompt': prompt}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      // Nếu API trả về image_base64
      if (data.containsKey('image_base64')) {
        return ImageResult.fromBase64(data['image_base64']);
      }
      // Nếu API trả về image_url (demo hoặc lỗi)
      if (data.containsKey('image_url')) {
        return ImageResult.fromUrl(data['image_url']);
      }
    }
    return null;
  }
}