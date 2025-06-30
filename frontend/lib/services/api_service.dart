import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/image_response.dart';

class ApiService {
  static const String baseUrl = "http://127.0.0.1:8000";

  static Future<ImageResponse> generateImage(String prompt, int width, int height) async {
    final url = Uri.parse('$baseUrl/generate-image');
    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "prompt": prompt,
        "width": width,
        "height": height,
      }),
    );
    if (response.statusCode == 200) {
      return ImageResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception(jsonDecode(response.body)['detail'] ?? 'API error');
    }
  }

  static Future<http.Response> downloadImage(String downloadUrl) async {
    final url = Uri.parse('$baseUrl$downloadUrl');
    return await http.get(url);
  }

  static Future<String> getShareLink(String shareUrl) async {
    final url = Uri.parse('$baseUrl$shareUrl');
    final response = await http.get(url);
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['share_link'] ?? '';
    } else {
      throw Exception('Share failed');
    }
  }
}
