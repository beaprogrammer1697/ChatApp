import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/chat_list_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Note: For a real app, generate firebase_options.dart using FlutterFire CLI.
  // Example initialization using default configuration
  try {
    await Firebase.initializeApp();
  } catch(e) {
    debugPrint("Firebase init failed (likely missing config): $e");
  }

  await apiService.init();

  runApp(const ChatApp());
}

class ChatApp extends StatelessWidget {
  const ChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    // If token exists we can try to skip login, but for simplicity:
    return MaterialApp(
      title: 'Flutter Chat App',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
      routes: {
        '/login': (context) => const LoginScreen(),
        '/chat_list': (context) => const ChatListScreen(),
      },
      debugShowCheckedModeBanner: false,
    );
  }
}
