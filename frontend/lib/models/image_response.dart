class ImageResponse {
  final String imageBase64;
  final String downloadUrl;
  final String shareUrl;

  ImageResponse({
    required this.imageBase64,
    required this.downloadUrl,
    required this.shareUrl,
  });

  factory ImageResponse.fromJson(Map<String, dynamic> json) {
    return ImageResponse(
      imageBase64: json['image_base64'] ?? '',
      downloadUrl: json['download_url'] ?? '',
      shareUrl: json['share_url'] ?? '',
    );
  }
}
