class ImageResponse {
  final String? imageBase64;
  final String? error;

  ImageResponse({this.imageBase64, this.error});

  factory ImageResponse.fromJson(Map<String, dynamic> json) {
    return ImageResponse(
      imageBase64: json['image_base64'],  
      error: json['error'],
    );
  }
}
