// Read-only input-source audit. Build on macOS: clang -framework Carbon this.c -o /tmp/adv360-layouts
#include <Carbon/Carbon.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const char *names[] = {"N1","N2","N3","N4","N5","N6","N7","N8","N9","N0",
        "KP_N1","KP_N2","KP_N3","KP_N4","KP_N5","KP_N6","KP_N7","KP_N8","KP_N9","KP_N0",
        "DOT","COMMA","KP_DOT","KP_PLUS","KP_MINUS","KP_MULTIPLY","KP_DIVIDE","KP_EQUAL","EQUAL","SEMI","Y","Z"};
    const UInt16 codes[] = {18,19,20,21,23,22,26,28,25,29,83,84,85,86,87,88,89,91,92,82,
        47,43,65,69,78,67,75,81,24,41,16,6};
    CFArrayRef sources = TISCreateInputSourceList(NULL, true);
    for (CFIndex i = 0; i < CFArrayGetCount(sources); i++) {
        TISInputSourceRef source = (TISInputSourceRef)CFArrayGetValueAtIndex(sources, i);
        CFStringRef id = TISGetInputSourceProperty(source, kTISPropertyInputSourceID);
        char sid[256];
        if (!id || !CFStringGetCString(id, sid, sizeof(sid), kCFStringEncodingUTF8)) continue;
        if (strcmp(sid,"com.apple.keylayout.ABC") && strcmp(sid,"com.apple.keylayout.US") && strcmp(sid,"com.apple.keylayout.Czech")) continue;
        CFDataRef data = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData);
        if (!data) continue;
        printf("%s (keyboard type %u)\n", sid, (unsigned)LMGetKbdType());
        for (unsigned n = 0; n < sizeof(codes)/sizeof(*codes); n++) {
            UInt32 dead = 0; UniChar chars[16]; UniCharCount len = 0;
            OSStatus status = UCKeyTranslate((const UCKeyboardLayout *)CFDataGetBytePtr(data),
                codes[n], kUCKeyActionDown, 0, LMGetKbdType(), kUCKeyTranslateNoDeadKeysMask,
                &dead, 16, &len, chars);
            CFStringRef out = CFStringCreateWithCharacters(NULL, chars, len);
            char result[128] = {0};
            CFStringGetCString(out, result, sizeof(result), kCFStringEncodingUTF8);
            printf("  %-12s %s (status %d)\n", names[n], result, (int)status);
            CFRelease(out);
        }
    }
    CFRelease(sources);
    return 0;
}
