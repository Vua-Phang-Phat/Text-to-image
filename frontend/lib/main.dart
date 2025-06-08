import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Text-to-Image',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true, // Nếu bạn muốn Material3
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
