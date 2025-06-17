class ImageResponse {
  final String imageBase64;

  ImageResponse({required this.imageBase64});

  factory ImageResponse.fromJson(Map<String, dynamic> json) {
    return ImageResponse(
      imageBase64: json['image_base64'] ?? '',
    );
  }
}
