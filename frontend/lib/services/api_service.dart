import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/image_response.dart';

class ApiService {
  static const String baseUrl = 'http://192.168.1.40:8000';

  static Future<ImageResponse> generateImage(String prompt, int width, int height) async {
    final response = await http.post(
      Uri.parse('$baseUrl/generate-image'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'prompt': prompt,
        'width': width,
        'height': height,
      }),
    );

    if (response.statusCode == 200) {
      return ImageResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Lỗi sinh ảnh: ${response.body}');
    }
  }
}
