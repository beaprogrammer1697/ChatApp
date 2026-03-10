import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000'; // For Android emulator, use localhost for iOS or web
  static const String wsUrl = 'ws://10.0.2.2:8000';

  String? _token;
  WebSocketChannel? _channel;
  
  Function(Map<String, dynamic>)? onMessageReceived;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('access_token');
  }

  Future<bool> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/token'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': username, 'password': password},
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _token = data['access_token'];
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', _token!);
      return true;
    }
    return false;
  }
  
  Future<bool> register(String username, String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'email': email, 'password': password}),
    );
    return response.statusCode == 201;
  }

  void connectWebSocket() {
    if (_token == null) return;
    _channel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/ws/$_token'),
    );

    _channel!.stream.listen((message) {
      final decoded = jsonDecode(message);
      if (onMessageReceived != null) {
        onMessageReceived!(decoded);
      }
    });
  }

  void disconnectWebSocket() {
    _channel?.sink.close();
  }

  Future<List<dynamic>> getMessages({String? otherUserId, String? groupId}) async {
    String url = '$baseUrl/messages?';
    if (otherUserId != null) url += 'other_user_id=$otherUserId&';
    if (groupId != null) url += 'group_id=$groupId&';
    
    final response = await http.get(
      Uri.parse(url),
      headers: {'Authorization': 'Bearer $_token'},
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  Future<bool> sendMessage(String content, {String? receiverId, String? groupId}) async {
    final payload = {
      'content': content,
      'receiver_id': receiverId,
      'group_id': groupId,
    };
    
    final response = await http.post(
      Uri.parse('$baseUrl/messages'),
      headers: {
        'Authorization': 'Bearer $_token',
        'Content-Type': 'application/json'
      },
      body: jsonEncode(payload),
    );
    return response.statusCode == 200;
  }

  Future<void> updateFCMToken(String token) async {
    if (_token == null) return;
    await http.post(
      Uri.parse('$baseUrl/users/me/fcm'),
      headers: {
        'Authorization': 'Bearer $_token',
        'Content-Type': 'application/json'
      },
      body: jsonEncode({'fcm_token': token}),
    );
  }
}

final apiService = ApiService();
