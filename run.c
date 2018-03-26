/* vim: set expandtab tabstop=4 softtabstop=4 shiftwidth=4: */
/*
 * Copyright © 2014 Intel Corporation
 * Copyright © 2015 Advanced Micro Devices, Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice (including the next
 * paragraph) shall be included in all copies or substantial portions of the
 * Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

/* for memmem(). The man page doesn't say __USE_GNU... */
/* also for asprintf() */
#define _GNU_SOURCE

#include <time.h>
#include <stdio.h>
#include <fcntl.h>
#include <assert.h>
#include <signal.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <ftw.h>

#include <epoxy/gl.h>
#include <epoxy/egl.h>
#include <gbm.h>
#include <omp.h>

#define unlikely(x) __builtin_expect(!!(x), 0)

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

struct context_info {
    char *extension_string;
    int extension_string_len;
    int max_glsl_version;
};

enum shader_type {
    TYPE_NONE,
    TYPE_CORE,
    TYPE_COMPAT,
    TYPE_ES,
    TYPE_VP,
    TYPE_FP,
};

struct shader {
    const char *text;
    int length;
    int type;
};

struct binding_list {
    char *name;
    GLint index;
    struct binding_list *prev;
};

static bool
extension_in_string(const char *haystack, const char *needle)
{
    const unsigned needle_len = strlen(needle);

    if (needle_len == 0)
        return false;

    while (true) {
        const char *const s = strstr(haystack, needle);

        if (s == NULL)
            return false;

        if (s[needle_len] == ' ' || s[needle_len] == '\0')
            return true;

        /* strstr found an extension whose name begins with
         * needle, but whose name is not equal to needle.
         * Restart the search at s + needle_len so that we
         * don't just find the same extension again and go
         * into an infinite loop.
         */
        haystack = s + needle_len;
    }

    return false;
}

#define SKIP_SPACES(str) while (*(str) == ' ') str++

static struct shader *
get_shaders(const struct context_info *core, const struct context_info *compat,
            const struct context_info *es,
            const char *text, size_t text_size,
            enum shader_type *type, unsigned *num_shaders,
            bool *use_separate_shader_objects,
            const char *shader_name, struct binding_list *binding)
{
    static const char *req = "[require]";
    static const char *gl_req = "\nGL >= ";
    static const char *glsl_req = "\nGLSL >= ";
    static const char *glsl_es_req = "\nGLSL ES >= ";
    static const char *fp_req = "\nGL_ARB_fragment_program";
    static const char *vp_req = "\nGL_ARB_vertex_program";
    static const char *sso_req = "\nSSO ENABLED";
    static const char *binding_req = "\nBindAttribLoc";
    static const char *gs = "geometry shader]\n";
    static const char *fs = "fragment ";
    static const char *vs = "vertex ";
    static const char *tcs = "tessellation control shader]\n";
    static const char *tes = "tessellation evaluation shader]\n";
    static const char *cs = "compute shader]\n";
    static const char *shder = "shader]\n";
    static const char *program = "program]\n";
    static const char *test = "test]\n";
    const char *end_text = text + text_size;

    *use_separate_shader_objects = false;

    /* Find the [require] block and parse it first. */
    text = memmem(text, end_text - text, req, strlen(req)) + strlen(req);

    /* Skip the GL >= x.y line if present. */
    if (memcmp(text, gl_req, strlen(gl_req)) == 0) {
        text += strlen(gl_req) + 3; /* for x.y */
    }

    if (memcmp(text, glsl_req, strlen(glsl_req)) == 0) {
        text += strlen(glsl_req);
        long major = strtol(text, (char **)&text, 10);
        long minor = strtol(text + 1, (char **)&text, 10);
        long version = major * 100 + minor;

        if (version <= 130) {
            if (unlikely(version > compat->max_glsl_version)) {
                fprintf(stderr, "SKIP: %s requires GLSL %ld\n",
                        shader_name, version);
                return NULL;
            }
            *type = TYPE_COMPAT;
        } else {
            if (unlikely(version > core->max_glsl_version)) {
                fprintf(stderr, "SKIP: %s requires GLSL %ld\n",
                        shader_name, version);
                return NULL;
            }
            *type = TYPE_CORE;
        }
    } else if (memcmp(text, glsl_es_req, strlen(glsl_es_req)) == 0) {
        text += strlen(glsl_es_req);
        long major = strtol(text, (char **)&text, 10);
        long minor = strtol(text + 1, (char **)&text, 10);
        long version = major * 100 + minor;

        if (unlikely(version > es->max_glsl_version)) {
            fprintf(stderr, "SKIP: %s requires GLSL ES %ld\n",
                    shader_name, version);
            return NULL;
        }
        *type = TYPE_ES;
    } else if (memcmp(text, fp_req, strlen(fp_req)) == 0) {
        *type = TYPE_FP;
    } else if (memcmp(text, vp_req, strlen(vp_req)) == 0) {
        *type = TYPE_VP;
    } else {
        fprintf(stderr, "ERROR: Unexpected token in %s\n", shader_name);
        return NULL;
    }

    const struct context_info *info = *type == TYPE_CORE ? core : compat;

    const char *extension_text = text;

    while ((extension_text = memmem(extension_text, end_text - extension_text,
                                    "\nGL_", strlen("\nGL_"))) != NULL) {
        extension_text += 1;
        const char *newline = memchr(extension_text, '\n',
                                     end_text - extension_text);

        if (memmem(info->extension_string, info->extension_string_len,
                   extension_text, newline - extension_text) == NULL) {
            fprintf(stderr, "SKIP: %s requires unavailable extension %.*s\n",
                    shader_name, (int)(newline - extension_text), extension_text);
            return NULL;
        }
        if (memcmp(extension_text, sso_req, strlen(sso_req)) == 0) {
            *use_separate_shader_objects = true;
        }
    }

    /* process binding */
    struct binding_list *binding_prev = binding = NULL;
    const char *pre_binding_text = text;

    /* binding = NULL if there's no binding required */
    binding = NULL;
    while ((pre_binding_text = memmem(pre_binding_text, end_text - pre_binding_text,
                                      binding_req, strlen(binding_req))) != NULL) {
        pre_binding_text += strlen(binding_req);

        const char *newline = memchr(pre_binding_text, '\n', end_text - pre_binding_text);

        SKIP_SPACES(pre_binding_text);

        char *endword = memchr(pre_binding_text, ' ', newline - pre_binding_text);

        /* if there's no more space in the same line */
        if (!endword) {
            fprintf(stderr, "SKIP: can't find attr index for this binding\n");
            continue;
        }

        char *binding_name = calloc(1, endword - pre_binding_text + 1);

        strncpy(binding_name, pre_binding_text, endword - pre_binding_text);

        pre_binding_text = endword;

        SKIP_SPACES(pre_binding_text);
        if (*pre_binding_text == '\n') {
            fprintf(stderr, "SKIP: can't find attr variable name for this binding\n");
            continue;
        }

        endword = memchr(pre_binding_text, ' ', newline - pre_binding_text);

        if (!endword)
            endword = (char *)newline;

        char *index_string = calloc(1, endword - pre_binding_text + 1);
        strncpy(index_string, pre_binding_text, endword - pre_binding_text);

        struct binding_list *binding_new = malloc(sizeof(struct binding_list));

        binding_new->index = strtol(index_string, NULL, 10);
        binding_new->name = binding_name;
        binding_new->prev = binding_prev;
        binding = binding_prev = binding_new;

        free(index_string);

        fprintf(stdout,
                "LOG: glBindAttribLocation(prog, %d, \"%s\") will be executed before linking\n",
                binding_new->index, binding_new->name);
    }

    /* Find the shaders. */
    unsigned shader_size = 3;
    struct shader *shader = malloc(shader_size * sizeof(struct shader));
    unsigned i = 0;
    while ((text = memmem(text, end_text - text, "\n[", strlen("\n["))) != NULL) {
        const char *save_text = text;
        text += strlen("\n[");

        if (shader_size == i)
            shader = realloc(shader, ++shader_size * sizeof(struct shader));

        if (memcmp(text, fs, strlen(fs)) == 0) {
            text += strlen(fs);
            if (memcmp(text, shder, strlen(shder)) == 0) {
                shader[i].type = GL_FRAGMENT_SHADER;
                text += strlen(shder);
            } else if (memcmp(text, program, strlen(program)) == 0) {
                shader[i].type = GL_FRAGMENT_PROGRAM_ARB;
                text += strlen(program);
            }
            shader[i].text = text;
        } else if (memcmp(text, vs, strlen(vs)) == 0) {
            text += strlen(vs);
            if (memcmp(text, shder, strlen(shder)) == 0) {
                shader[i].type = GL_VERTEX_SHADER;
                text += strlen(shder);
            } else if (memcmp(text, program, strlen(program)) == 0) {
                shader[i].type = GL_VERTEX_PROGRAM_ARB;
                text += strlen(program);
            }
            shader[i].text = text;
        } else if (memcmp(text, gs, strlen(gs)) == 0) {
            text += strlen(gs);
            shader[i].type = GL_GEOMETRY_SHADER;
            shader[i].text = text;
        } else if (memcmp(text, tcs, strlen(tcs)) == 0) {
            text += strlen(tcs);
            shader[i].type = GL_TESS_CONTROL_SHADER;
            shader[i].text = text;
        } else if (memcmp(text, tes, strlen(tes)) == 0) {
            text += strlen(tes);
            shader[i].type = GL_TESS_EVALUATION_SHADER;
            shader[i].text = text;
        } else if (memcmp(text, cs, strlen(cs)) == 0) {
            text += strlen(cs);
            shader[i].type = GL_COMPUTE_SHADER;
            shader[i].text = text;
        } else if (memcmp(text, test, strlen(test)) == 0) {
            shader[i - 1].length = save_text + 1 - shader[i - 1].text;
            goto out;
        } else {
            fprintf(stderr, "ERROR: Unexpected token in %s\n", shader_name);
            free(shader);
            return NULL;
        }

        if (i != 0)
            shader[i - 1].length = save_text + 1 - shader[i - 1].text;
        i++;
    }

    shader[i - 1].length = end_text - shader[i - 1].text;

 out:
    *num_shaders = i;
    return shader;
}

static void
callback(GLenum source, GLenum type, GLuint id, GLenum severity, GLsizei length,
         const GLchar *message, const void *userParam)
{
    assert(source == GL_DEBUG_SOURCE_SHADER_COMPILER);
    assert(type == GL_DEBUG_TYPE_OTHER);
    assert(severity == GL_DEBUG_SEVERITY_NOTIFICATION);

    const char *const *shader_name = userParam;
    printf("%s - %s\n", *shader_name, message);
}

static unsigned shader_test_size = 1 << 15; /* next-pow-2(num shaders in db) */
static unsigned shader_test_length;
static struct shader_test {
    char *filename;
    off_t filesize;
} *shader_test;

static int
gather_shader_test(const char *fpath, const struct stat *sb, int typeflag)
{
    static const char *ext = ".shader_test";

    if (strlen(fpath) >= strlen(ext) &&
        memcmp(fpath + strlen(fpath) - strlen(ext), ext, strlen(ext)) == 0) {
        if (unlikely(!S_ISREG(sb->st_mode))) {
            fprintf(stderr, "ERROR: %s is not a regular file\n", fpath);
            return -1;
        }

        if (unlikely(shader_test_size <= shader_test_length)) {
            shader_test_size *= 2;
            shader_test = realloc(shader_test, shader_test_size * sizeof(struct shader_test));
        }
        shader_test[shader_test_length].filename = malloc(strlen(fpath) + 1);
        memcpy(shader_test[shader_test_length].filename, fpath, strlen(fpath) + 1);
        shader_test[shader_test_length].filesize = sb->st_size;
        shader_test_length++;
    }

    return 0;
}

const char **current_shader_names;
int max_threads;

#define sigputs(str) write(STDERR_FILENO, str, strlen(str))

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-result"
static void
abort_handler(int signo)
{
    if (current_shader_names) {
        sigputs("\n => CRASHED <= while processing these shaders:\n\n");
        for (int i = 0; i < max_threads; i++) {
            if (current_shader_names[i]) {
                sigputs("    ");
                sigputs(current_shader_names[i]);
                sigputs("\n");
            }
        }
    } else {
       sigputs("\n => CRASHED <= during final teardown.\n");
    }
    sigputs("\n");
    _exit(-1);
}
#pragma GCC diagnostic pop

struct platform {
    const char *name;
    const char *pci_id;
};

const struct platform platforms[] = {
    "i965", "0x2A02",
    "g4x",  "0x2A42",
    "ilk",  "0x0042",
    "snb",  "0x0126",
    "ivb",  "0x016a",
    "hsw",  "0x0D2E",
    "byt",  "0x0F33",
    "bdw",  "0x162E",
    "skl",  "0x191D",
};

void print_usage(const char *prog_name)
{
    fprintf(stderr,
            "Usage: %s [-d <device>] [-j <max_threads>] [-o <driver>] [-p <pci"
            " id or platform name> [-b] <directories and *.shader_test files>\n",
            prog_name);
}

static void addenv(const char *name, const char *value)
{
    const char *orig = getenv(name);
    if (orig) {
        char *newval;
        asprintf(&newval, "%s,%s", orig, value);
        setenv(name, newval, 1);
        free(newval);
    } else {
        setenv(name, value, 1);
    }
}

static int
get_glsl_version(void)
{
    const char *es_prefix = "OpenGL ES GLSL ES ";
    const char *ver = glGetString(GL_SHADING_LANGUAGE_VERSION);
    unsigned major = 0, minor = 0;

    if (strstr(ver, es_prefix) == ver)
        ver += strlen(es_prefix);

    sscanf(ver, "%u.%u", &major, &minor);
    return major * 100 + minor;
}

static EGLContext
create_context(EGLDisplay egl_dpy, EGLConfig cfg, enum shader_type type)
{
    static const EGLint attribs[] = {
        EGL_CONTEXT_OPENGL_PROFILE_MASK_KHR,
        EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT_KHR,
        EGL_CONTEXT_MAJOR_VERSION_KHR, 3,
        EGL_CONTEXT_MINOR_VERSION_KHR, 2,
        EGL_NONE
    };
    static const EGLint es_attribs[] = {
        EGL_CONTEXT_CLIENT_VERSION, 2,
        EGL_NONE
    };
    switch (type) {
    case TYPE_CORE: {
        eglBindAPI(EGL_OPENGL_API);
        EGLContext core_ctx =
                eglCreateContext(egl_dpy, cfg, EGL_NO_CONTEXT, attribs);

        if (core_ctx == EGL_NO_CONTEXT) {
            static const EGLint attribs_31[] = {
                EGL_CONTEXT_MAJOR_VERSION_KHR, 3,
                EGL_CONTEXT_MINOR_VERSION_KHR, 1,
                EGL_NONE
            };
            core_ctx = eglCreateContext(egl_dpy, cfg, EGL_NO_CONTEXT, attribs_31);
        }

        return core_ctx;
    }
    case TYPE_COMPAT:
        eglBindAPI(EGL_OPENGL_API);
        return eglCreateContext(egl_dpy, cfg, EGL_NO_CONTEXT, &attribs[6]);
    case TYPE_ES:
        eglBindAPI(EGL_OPENGL_ES_API);
        return eglCreateContext(egl_dpy, cfg, EGL_NO_CONTEXT, es_attribs);
    default:
        return NULL;
    }
}

int
main(int argc, char **argv)
{
    char device_path[64];
    int device_id = 0;
    int opt;
    bool generate_prog_bin = 0;

    max_threads = omp_get_max_threads();

    while ((opt = getopt(argc, argv, "d:j:o:p:b")) != -1) {
        switch(opt) {
        case 'd': {
            char *endptr;

            device_id = strtol(optarg, &endptr, 10);
            if (endptr == optarg) {
                fprintf(stderr, "Invalid device ID.\n");
                return -1;
            }
            break;
        }
        case 'o':
            printf("### Overriding driver for %s ###\n", optarg);
            setenv("MESA_LOADER_DRIVER_OVERRIDE", optarg, 1);
            break;
        case 'p': {
            const struct platform *platform = NULL;
            for (unsigned i = 0; i < ARRAY_SIZE(platforms); i++) {
                if (strcasecmp(optarg, platforms[i].name) == 0) {
                    platform = platforms + i;
                    break;
                }
            }

            if (platform) {
                printf("### Compiling for %s(PCI_ID=%s) ###\n", platform->name,
                       platform->pci_id);
                setenv("INTEL_DEVID_OVERRIDE", platform->pci_id, 1);
                break;
            }

            /* Also allow a numeric PCI ID */
            if (strtol(optarg, NULL, 0) > 0) {
                setenv("INTEL_DEVID_OVERRIDE", optarg, 1);
                printf("### Compiling for PCI_ID=%s ###\n", optarg);
                break;
            }

            fprintf(stderr, "Invalid platform.\nValid platforms are:");
            for (unsigned i = 0; i < ARRAY_SIZE(platforms); i++)
                fprintf(stderr, " %s", platforms[i].name);

            fprintf(stderr, "\n");
            fprintf(stderr, "Or\nPCI-ID of other supported platform.\n");
            return -1;
        }
        case 'j':
            max_threads = atoi(optarg);
            break;
        case 'b':
            generate_prog_bin = 1;
            break;
        default:
            fprintf(stderr, "Unknown option: %x\n", opt);
            print_usage(argv[0]);
            return -1;
        }
    }

    if (unlikely(optind >= argc)) {
        fprintf(stderr, "No directories specified\n");
        print_usage(argv[0]);
        return -1;
    }

    setenv("allow_glsl_extension_directive_midshader", "true", 1);
    setenv("shader_precompile", "true", 1);
    setenv("MESA_GLSL_CACHE_DISABLE", "true", 1);
    setenv("GALLIUM_THREAD", "0", 1);
    addenv("ST_DEBUG", "precompile");
    addenv("R600_DEBUG", "precompile");
    addenv("FD_MESA_DEBUG", "shaderdb");

    const char *client_extensions = eglQueryString(EGL_NO_DISPLAY,
                                                   EGL_EXTENSIONS);
    if (!client_extensions) {
        fprintf(stderr, "ERROR: Missing EGL_EXT_client_extensions\n");
        return -1;
    }

    if (!extension_in_string(client_extensions, "EGL_MESA_platform_gbm")) {
        fprintf(stderr, "ERROR: Missing EGL_MESA_platform_gbm\n");
        return -1;
    }

    int ret = 0;

    snprintf(device_path, sizeof(device_path),
             "/dev/dri/renderD%d", device_id + 128);

    int fd = open(device_path, O_RDWR);
    if (unlikely(fd < 0)) {
        fprintf(stderr, "ERROR: Couldn't open %s\n", device_path);
        return -1;
    }

    struct gbm_device *gbm = gbm_create_device(fd);
    if (unlikely(gbm == NULL)) {
        fprintf(stderr, "ERROR: Couldn't create gbm device\n");
        ret = -1;
        goto close_fd;
    }

    EGLDisplay egl_dpy = eglGetPlatformDisplayEXT(EGL_PLATFORM_GBM_MESA,
                                                  gbm, NULL);
    if (unlikely(egl_dpy == EGL_NO_DISPLAY)) {
        fprintf(stderr, "ERROR: eglGetDisplay() failed\n");
        ret = -1;
        goto destroy_gbm_device;
    }

    if (unlikely(!eglInitialize(egl_dpy, NULL, NULL))) {
        fprintf(stderr, "ERROR: eglInitialize() failed\n");
        ret = -1;
        goto destroy_gbm_device;
    }

    static const char *egl_extension[] = {
            "EGL_KHR_create_context",
            "EGL_KHR_surfaceless_context"
    };
    const char *egl_extension_string = eglQueryString(egl_dpy, EGL_EXTENSIONS);
    for (int i = 0; i < ARRAY_SIZE(egl_extension); i++) {
        if (!extension_in_string(egl_extension_string, egl_extension[i])) {
            fprintf(stderr, "ERROR: Missing %s\n", egl_extension[i]);
            ret = -1;
            goto egl_terminate;
        }
    }

    static const EGLint config_attribs[] = {
        EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
        EGL_NONE
    };
    EGLConfig cfg;
    EGLint count;

    if (!eglChooseConfig(egl_dpy, config_attribs, &cfg, 1, &count) ||
        count == 0) {
        fprintf(stderr, "ERROR: eglChooseConfig() failed\n");
        ret = -1;
        goto egl_terminate;
    }

    static struct context_info core = { 0 }, compat = { 0 }, es = { 0 };

    EGLContext es_ctx = create_context(egl_dpy, cfg, TYPE_ES);
    if (es_ctx != EGL_NO_CONTEXT &&
        eglMakeCurrent(egl_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, es_ctx)) {

        es.extension_string = (char *)glGetString(GL_EXTENSIONS);
        es.extension_string_len = strlen(es.extension_string);

        es.max_glsl_version = get_glsl_version();

        if (!extension_in_string(es.extension_string, "GL_KHR_debug")) {
            fprintf(stderr, "ERROR: Missing GL_KHR_debug\n");
            ret = -1;
            goto egl_terminate;
        }
    }

    EGLContext core_ctx = create_context(egl_dpy, cfg, TYPE_CORE);

    if (core_ctx != EGL_NO_CONTEXT &&
        eglMakeCurrent(egl_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, core_ctx)) {
        int num_extensions;
        char *gl_extension_string;

        glGetIntegerv(GL_NUM_EXTENSIONS, &num_extensions);

        size_t extension_string_size = num_extensions * 26;
        core.extension_string = malloc(extension_string_size);
        gl_extension_string = core.extension_string;
        char *end_extension_string = core.extension_string +
                                     extension_string_size;

        for (int i = 0; i < num_extensions; i++) {
            const char *ext = glGetStringi(GL_EXTENSIONS, i);
            size_t len = strlen(ext);

            if (unlikely(gl_extension_string + len + 1 >= end_extension_string)) {
                extension_string_size *= 2;
                size_t extension_string_offset = gl_extension_string -
                                                 core.extension_string;
                core.extension_string = realloc(core.extension_string,
                                                extension_string_size);
                gl_extension_string = core.extension_string +
                                   extension_string_offset;
                end_extension_string = core.extension_string +
                                       extension_string_size;
            }

            memcpy(gl_extension_string, ext, len);
            gl_extension_string[len] = ' ';
            gl_extension_string += len + 1;
        }
        gl_extension_string[-1] = '\0';
        core.extension_string_len = gl_extension_string - 1 -
                                    core.extension_string;

        core.max_glsl_version = get_glsl_version();

        if (!extension_in_string(core.extension_string, "GL_KHR_debug")) {
            fprintf(stderr, "ERROR: Missing GL_KHR_debug\n");
            ret = -1;
            goto egl_terminate;
        }
    }

    EGLContext compat_ctx = create_context(egl_dpy, cfg, TYPE_COMPAT);
    if (compat_ctx == EGL_NO_CONTEXT) {
        fprintf(stderr, "ERROR: eglCreateContext() failed\n");
        ret = -1;
        goto egl_terminate;
    }

    if (!eglMakeCurrent(egl_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, compat_ctx)) {
        fprintf(stderr, "ERROR: eglMakeCurrent() failed\n");
        ret = -1;
        goto egl_terminate;
    } else {
        compat.extension_string = (char *)glGetString(GL_EXTENSIONS);
        compat.extension_string_len = strlen(compat.extension_string);

        compat.max_glsl_version = get_glsl_version();

        if (!extension_in_string(compat.extension_string, "GL_KHR_debug")) {
            fprintf(stderr, "ERROR: Missing GL_KHR_debug\n");
            ret = -1;
            goto egl_terminate;
        }
    }

    shader_test = malloc(shader_test_size * sizeof(struct shader_test));
    for (int i = optind; i < argc; i++) {
        ftw(argv[i], gather_shader_test, 100);
    }

    current_shader_names = calloc(max_threads, sizeof(const char *));

    if (signal(SIGABRT, abort_handler) == SIG_ERR)
        fprintf(stderr, "WARNING: could not install SIGABRT handler.\n");
    if (signal(SIGSEGV, abort_handler) == SIG_ERR)
        fprintf(stderr, "WARNING: could not install SIGSEGV handler.\n");

    #pragma omp parallel if(max_threads > 1 && shader_test_length > max_threads)
    {
        const char *current_shader_name;
        unsigned shaders_compiled = 0;
        unsigned ctx_switches = 0;
        struct timespec start, end;
        clock_gettime(CLOCK_THREAD_CPUTIME_ID, &start);

        EGLContext es_ctx = create_context(egl_dpy, cfg, TYPE_ES);
        if (es_ctx != EGL_NO_CONTEXT &&
            eglMakeCurrent(egl_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, es_ctx)) {
            glEnable(GL_DEBUG_OUTPUT);
            glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
            glDebugMessageControl(GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE,
                                  0, NULL, GL_FALSE);
            glDebugMessageControl(GL_DEBUG_SOURCE_SHADER_COMPILER,
                                  GL_DEBUG_TYPE_OTHER,
                                  GL_DEBUG_SEVERITY_NOTIFICATION, 0, NULL,
                                  GL_TRUE);
            glDebugMessageCallback(callback, &current_shader_name);
        }

        EGLContext core_ctx = create_context(egl_dpy, cfg, TYPE_CORE);
        if (core_ctx != EGL_NO_CONTEXT &&
            eglMakeCurrent(egl_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, core_ctx)) {
            glEnable(GL_DEBUG_OUTPUT);
            glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
            glDebugMessageControl(GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE,
                                  0, NULL, GL_FALSE);
            glDebugMessageControl(GL_DEBUG_SOURCE_SHADER_COMPILER,
                                  GL_DEBUG_TYPE_OTHER,
                                  GL_DEBUG_SEVERITY_NOTIFICATION, 0, NULL,
                                  GL_TRUE);
            glDebugMessageCallback(callback, &current_shader_name);
        }

        EGLContext compat_ctx = create_context(egl_dpy, cfg, TYPE_COMPAT);
        if (compat_ctx == EGL_NO_CONTEXT) {
            fprintf(stderr, "ERROR: eglCreateContext() failed\n");
            exit(-1);
        }

        enum shader_type current_type = TYPE_NONE;
        if (!eglMakeCurrent(egl_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE,
                            compat_ctx)) {
            fprintf(stderr, "ERROR: eglMakeCurrent() failed\n");
        }

        glEnable(GL_DEBUG_OUTPUT);
        glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
        glDebugMessageControl(GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE,
                              0, NULL, GL_FALSE);
        glDebugMessageControl(GL_DEBUG_SOURCE_SHADER_COMPILER,
                              GL_DEBUG_TYPE_OTHER,
                              GL_DEBUG_SEVERITY_NOTIFICATION, 0, NULL, GL_TRUE);
        glDebugMessageCallback(callback, &current_shader_name);

        #pragma omp for schedule(dynamic)
        for (int i = 0; i < shader_test_length; i++) {
            current_shader_name = shader_test[i].filename;
            current_shader_names[omp_get_thread_num()] = current_shader_name;

            int fd = open(current_shader_name, O_RDONLY);
            if (unlikely(fd == -1)) {
                perror("open");
                continue;
            }

            char *text = mmap(NULL, shader_test[i].filesize, PROT_READ,
                              MAP_PRIVATE, fd, 0);
            if (unlikely(text == MAP_FAILED)) {
                perror("mmap");
                continue;
            }

            if (unlikely(close(fd) == -1)) {
                perror("close");
                continue;
            }

            enum shader_type type;
            unsigned num_shaders;
            bool use_separate_shader_objects;
            struct binding_list *binding;
            struct shader *shader = get_shaders(&core, &compat, &es,
                                                text, shader_test[i].filesize,
                                                &type, &num_shaders,
                                                &use_separate_shader_objects,
                                                current_shader_name, binding);
            if (unlikely(shader == NULL)) {
                continue;
            }

            if (current_type != type) {
                EGLContext ctx;

                ctx_switches++;

                switch (type) {
                case TYPE_ES:
                    eglBindAPI(EGL_OPENGL_ES_API);
                    ctx = es_ctx;
                    break;
                case TYPE_CORE:
                    eglBindAPI(EGL_OPENGL_API);
                    ctx = core_ctx;
                    break;
                default:
                    eglBindAPI(EGL_OPENGL_API);
                    ctx = compat_ctx;
                    break;
                }

                if (!eglMakeCurrent(egl_dpy, EGL_NO_SURFACE, EGL_NO_SURFACE,
                                    ctx)) {
                    fprintf(stderr, "ERROR: eglMakeCurrent() failed\n");
                    continue;
                }
            }
            current_type = type;

            /* If there's only one GLSL shader, mark it separable so
             * inputs and outputs aren't eliminated.
             */
            if (num_shaders == 1 && type != TYPE_VP && type != TYPE_FP)
                use_separate_shader_objects = true;

            if (use_separate_shader_objects) {
                for (unsigned i = 0; i < num_shaders; i++) {
                    const char *const_text;
                    unsigned size = shader[i].length + 1;
                    /* Using alloca crashes in the GLSL compiler.  */
                    char *text = malloc(size);
                    memset(text, 0, size);

                    /* Make it zero-terminated. */
                    memcpy(text, shader[i].text, shader[i].length);
                    text[shader[i].length] = 0;

                    const_text = text;
                    GLuint prog = glCreateShaderProgramv(shader[i].type, 1,
                                                         &const_text);

                    if (generate_prog_bin)
                        fprintf(stderr,
                                "Currently, program binary generation "
                                "doesn't support SSO.\n");

                    glDeleteProgram(prog);
                    free(text);
                }
            } else if (type == TYPE_CORE || type == TYPE_COMPAT || type == TYPE_ES) {
                GLuint prog = glCreateProgram();
                GLint param;

                for (unsigned i = 0; i < num_shaders; i++) {
                    GLuint s = glCreateShader(shader[i].type);
                    glShaderSource(s, 1, &shader[i].text, &shader[i].length);
                    glCompileShader(s);

                    glGetShaderiv(s, GL_COMPILE_STATUS, &param);
                    if (unlikely(!param)) {
                        GLchar log[4096];
                        GLsizei length;
                        glGetShaderInfoLog(s, 4096, &length, log);

                        fprintf(stderr, "ERROR: %s failed to compile:\n%s\n",
                                current_shader_name, log);
                    }
                    glAttachShader(prog, s);
                    glDeleteShader(s);
                }

                /* takes care of pre-bindings */
                while (binding != NULL) {
                    struct binding_list *prev = binding->prev;
                    glBindAttribLocation(prog, binding->index, binding->name);
                    free(binding->name);
                    free(binding);
                    binding = prev;
                }

                glLinkProgram(prog);

                glGetProgramiv(prog, GL_LINK_STATUS, &param);
                if (unlikely(!param)) {
                    GLchar log[4096];
                    GLsizei length;
                    glGetProgramInfoLog(prog, sizeof(log), &length, log);

                    fprintf(stderr, "ERROR: failed to link progam:\n%s\n",
                           log);
                } else if (generate_prog_bin) {
                    /* generating shader program binary */
                    char *prog_buf;
                    GLenum format;
                    GLsizei length = 0;
                    FILE *fp;

                    glGetProgramiv(prog, GL_PROGRAM_BINARY_LENGTH, &length);

                    if (glGetError() != GL_NO_ERROR) {
                        fprintf(stderr,
                                "ERROR: failed to generate a program binary "
                                "(invalid program size).\n");
                        continue;
                    }

                    prog_buf = (char *)malloc(length);

                    if (!prog_buf) {
                        fprintf(stderr,
                                "ERROR: failed to generate a program binary "
                                "(malloc failed)\n");
                        continue;
                    }

                    glGetProgramBinary(prog, length, &length, &format, prog_buf);
                    if (glGetError() != GL_NO_ERROR) {
                        fprintf(stderr,
                                "ERROR: failed to generate a program binary "
                                "(GetProgramBinary failed)\n");
                        free(prog_buf);
                        continue;
                    }

                    char *out_filename = malloc(strlen(current_shader_name) + 5);

                    strncpy(out_filename, current_shader_name,
                            strlen(current_shader_name) + 1);
                    out_filename = strcat(out_filename, ".bin");

                    fp = fopen(out_filename, "wb");
                    fprintf(stdout,
                            "\nBinary program has been successfully generated for %s.\n"
                            "\nWriting it to the file.....\n"
                            "===============================================\n"
                            "File Name : %s\nFormat : %d\nSize : %d Byte\n"
                            "===============================================\n\n",
                            current_shader_name, out_filename, format, length);

                    fwrite(prog_buf, sizeof(char), length, fp);
                    fclose(fp);
                    free(out_filename);
                    free(prog_buf);
                }

                glDeleteProgram(prog);
            } else {
                for (unsigned i = 0; i < num_shaders; i++) {
                    GLuint prog;
                    glGenProgramsARB(1, &prog);
                    glBindProgramARB(shader[i].type, prog);
                    glProgramStringARB(shader[i].type, GL_PROGRAM_FORMAT_ASCII_ARB,
                                       shader[i].length, shader[i].text);
                    glDeleteProgramsARB(1, &prog);
                    if (glGetError() == GL_INVALID_OPERATION) {
                        fprintf(stderr, "ERROR: %s failed to compile\n",
                                current_shader_name);
                    }
                }
            }
            shaders_compiled += num_shaders;

            current_shader_names[omp_get_thread_num()] = NULL;

            free(shader);
            free(shader_test[i].filename);

            if (unlikely(munmap(text, shader_test[i].filesize) == -1)) {
                perror("munmap");
                continue;
            }
        }

        eglDestroyContext(egl_dpy, compat_ctx);
        eglDestroyContext(egl_dpy, core_ctx);
        eglDestroyContext(egl_dpy, es_ctx);
        eglReleaseThread();

        clock_gettime(CLOCK_THREAD_CPUTIME_ID, &end);
        printf("Thread %d took %.2lf seconds and compiled %u shaders "
               "(not including SIMD16) with %u GL context switches\n",
               omp_get_thread_num(),
               (end.tv_sec - start.tv_sec) + 10e-9 * (end.tv_nsec - start.tv_nsec),
               shaders_compiled, ctx_switches);
    }

    free(current_shader_names);
    free(shader_test);
    free(core.extension_string);
    current_shader_names = NULL;

 egl_terminate:
    eglTerminate(egl_dpy);
 destroy_gbm_device:
    gbm_device_destroy(gbm);
 close_fd:
    close(fd);

    return ret;
}
