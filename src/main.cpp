#include <Geode/Geode.hpp>
#include <Geode/modify/PlayLayer.hpp>
#include <Geode/modify/GJBaseGameLayer.hpp>

#include <winsock2.h>
#include <ws2tcpip.h>
#include <string>
#include <vector>
#include <sstream>

#pragma comment(lib, "ws2_32.lib")

using namespace geode::prelude;

// ============================================
// Состояние бота
// ============================================
struct BotState {
    bool enabled = false;
    bool level_loaded = false;
    bool macro_ready = false;
    
    std::vector<std::pair<int, bool>> macro;  // (frame, is_click)
    size_t macro_index = 0;
    int current_frame = 0;
    
    SOCKET sock = INVALID_SOCKET;
};

static BotState g_bot;

// ============================================
// Сетевые хелперы
// ============================================
bool init_winsock() {
    WSADATA wsa;
    return WSAStartup(MAKEWORD(2, 2), &wsa) == 0;
}

bool connect_to_ai() {
    if (g_bot.sock != INVALID_SOCKET) return true;
    
    g_bot.sock = socket(AF_INET, SOCK_STREAM, 0);
    if (g_bot.sock == INVALID_SOCKET) return false;
    
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(42069);
    inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
    
    if (connect(g_bot.sock, (sockaddr*)&addr, sizeof(addr)) == 0) {
        log::info("[GD-AI] Connected to Python AI server");
        return true;
    }
    log::warn("[GD-AI] Cannot connect to AI (port 42069)");
    closesocket(g_bot.sock);
    g_bot.sock = INVALID_SOCKET;
    return false;
}

void send_json(const std::string& json) {
    if (g_bot.sock == INVALID_SOCKET) return;
    std::string msg = json + "\n";
    send(g_bot.sock, msg.c_str(), msg.size(), 0);
}

std::string recv_line() {
    if (g_bot.sock == INVALID_SOCKET) return "";
    
    std::string buffer;
    char c;
    while (true) {
        int r = recv(g_bot.sock, &c, 1, 0);
        if (r <= 0) return "";
        if (c == '\n') break;
        buffer += c;
        if (buffer.size() > 500000) break;
    }
    return buffer;
}

std::string escape_json(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (char c : s) {
        if (c == '"' || c == '\\') out += '\\';
        out += (c == '\n') ? ' ' : c;
        if (out.size() > 500000) break;
    }
    return out;
}

// ============================================
// Парсинг ответа от AI
// ============================================
void parse_macro_response(const std::string& json) {
    g_bot.macro.clear();
    
    auto macro_pos = json.find("\"macro\":[");
    if (macro_pos == std::string::npos) return;
    
    auto start = json.find('[', macro_pos);
    auto end = json.find(']', start);
    if (start == std::string::npos || end == std::string::npos) return;
    
    std::string arr = json.substr(start + 1, end - start - 1);
    
    size_t pos = 0;
    while ((pos = arr.find("\"frame\":", pos)) != std::string::npos) {
        int frame = 0;
        pos += 8;
        while (pos < arr.size() && arr[pos] >= '0' && arr[pos] <= '9') {
            frame = frame * 10 + (arr[pos] - '0');
            pos++;
        }
        g_bot.macro.push_back({frame, true});
    }
    
    log::info("[GD-AI] Loaded macro: {} clicks", g_bot.macro.size());
    g_bot.macro_ready = true;
    g_bot.macro_index = 0;
}

// ============================================
// ХУК 1: Старт уровня
// ============================================
class $modify(MyPlayLayer, PlayLayer) {
    bool init(GJGameLevel* level, bool useReplay, bool dontCreateObjects) {
        if (!PlayLayer::init(level, useReplay, dontCreateObjects))
            return false;
        
        g_bot.current_frame = 0;
        g_bot.macro.clear();
        g_bot.macro_ready = false;
        g_bot.level_loaded = false;
        
        if (g_bot.enabled && connect_to_ai()) {
            std::string ls = level->m_levelString;
            std::string req = "{\"cmd\":\"load_level\",\"level_string\":\"" + escape_json(ls) + "\"}";
            send_json(req);
            
            std::string resp = recv_line();
            log::info("[GD-AI] AI load response: {}", resp.substr(0, 100));
            
            send_json("{\"cmd\":\"generate_macro\"}");
            std::string macro_resp = recv_line();
            parse_macro_response(macro_resp);
            g_bot.level_loaded = true;
        }
        
        return true;
    }
    
    void playDeathEffect() {
        if (g_bot.enabled && g_bot.level_loaded) {
            float dx = 0, dy = 0;
            if (auto player = this->m_player1) {
                dx = player->getPositionX();
                dy = player->getPositionY();
            }
            
            std::ostringstream oss;
            oss << "{\"cmd\":\"death\",\"frame\":" << g_bot.current_frame 
                << ",\"x\":" << dx << ",\"y\":" << dy << "}";
            send_json(oss.str());
            
            std::string resp = recv_line();
            log::info("[GD-AI] AI death response: {}", resp.substr(0, 100));
            
            if (resp.find("\"status\":\"ok\"") != std::string::npos) {
                parse_macro_response(resp);
                this->resetLevel();
            }
        }
        
        PlayLayer::playDeathEffect();
    }
};

// ============================================
// ХУК 2: Каждый кадр
// ============================================
class $modify(MyGJBGL, GJBaseGameLayer) {
    void update(float dt) {
        GJBaseGameLayer::update(dt);
        
        if (!g_bot.enabled || !g_bot.macro_ready) return;
        
        g_bot.current_frame++;
        
        while (g_bot.macro_index < g_bot.macro.size()) {
            auto& [frame, is_click] = g_bot.macro[g_bot.macro_index];
            if (frame > g_bot.current_frame) break;
            if (frame == g_bot.current_frame && is_click) {
                if (auto player = this->m_player1) {
                    player->pushButton(PlayerButton::Jump);
                    g_bot.macro.insert(
                        g_bot.macro.begin() + g_bot.macro_index + 1,
                        {frame + 1, false}
                    );
                }
            }
            g_bot.macro_index++;
        }
    }
};

// ============================================
// ХУК 3: Включение по F6
// ============================================
class $modify(MyPlayLayer2, PlayLayer) {
    void update(float dt) {
        PlayLayer::update(dt);
        
        static bool f6_prev = false;
        bool f6_now = cocos2d::CCKeyboardDispatcher::get()->isKeyPressed(cocos2d::KEY_F6);
        if (f6_now && !f6_prev) {
            g_bot.enabled = !g_bot.enabled;
            log::info("[GD-AI] Bot {}", g_bot.enabled ? "ON" : "OFF");
            if (g_bot.enabled) init_winsock();
        }
        f6_prev = f6_now;
    }
};

$on_mod(Loaded) {
    log::info("[GD-AI] Mod loaded! F6 to toggle. Run ai/ipc_server.py first.");
    init_winsock();
}