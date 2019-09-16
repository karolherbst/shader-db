/*
 * Copyright © 2015-2017 Intel Corporation
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
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

#define _GNU_SOURCE /* for RTLD_NEXT */

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <stdarg.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <sys/sysmacros.h>
#include <dlfcn.h>
#include <i915_drm.h>

static void *(*libc_mmap)(void *addr, size_t len, int prot, int flags,
                          int fildes, off_t off);
static void *(*libc_mmap64)(void *addr, size_t len, int prot, int flags,
                            int fildes, off_t off);
static int (*libc_open)(const char *pathname, int flags, mode_t mode);
static int (*libc_open64)(const char *pathname, int flags, mode_t mode);
static int (*libc_close)(int fd);
static int (*libc_ioctl)(int fd, unsigned long request, void *argp);
static int (*libc_fstat)(int fd, struct stat *buf);
static int (*libc_fstat64)(int fd, struct stat64 *buf);
static int (*libc__fxstat)(int ver, int fd, struct stat *buf);
static int (*libc__fxstat64)(int ver, int fd, struct stat64 *buf);
static int (*libc_fcntl)(int fd, int cmd, int param);
static int (*libc_fcntl64)(int fd, int cmd, int param);
static ssize_t (*libc_readlink)(const char *pathname, char *buf, size_t bufsiz);

static int drm_fd = 0x0000BEEF;

#define DRM_MAJOR 226

#define SYSFS_PATH "/sys/dev/char/226:0/device/subsystem"

static int
dispatch_version(int fd, unsigned long request,
                 struct drm_version *version)
{
	static const char name[] = "i915";
	static const char date[] = "20160919";
	static const char desc[] = "Intel Graphics";

	version->version_major = 1;
	version->version_minor = 6;
	version->version_patchlevel = 0;

	if (version->name)
		strncpy(version->name, name, version->name_len);
	version->name_len = strlen(name);
	if (version->date)
		strncpy(version->date, date, version->date_len);
	version->date_len = strlen(date);
	if (version->desc)
		strncpy(version->desc, desc, version->desc_len);
	version->desc_len = strlen(desc);

	return 0;
}

__attribute__ ((visibility ("default"))) int
open(const char *path, int flags, ...)
{
       va_list args;
       mode_t mode;

       if (strcmp(path, "/dev/dri/renderD128") == 0)
	       return drm_fd;

       va_start(args, flags);
       mode = va_arg(args, int);
       va_end(args);

       return libc_open(path, flags, mode);
}

__attribute__ ((visibility ("default"))) int
open64(const char *path, int flags, ...)
{
       va_list args;
       mode_t mode;

       if (strcmp(path, "/dev/dri/renderD128") == 0)
	       return drm_fd;

       va_start(args, flags);
       mode = va_arg(args, int);
       va_end(args);

       return libc_open64(path, flags, mode);
}

__attribute__ ((visibility ("default"))) int
close(int fd)
{
	if (fd == drm_fd)
		return 0;

	return libc_close(fd);
}

__attribute__ ((visibility ("default"))) int
fstat(int fd, struct stat *buf)
{
	if (fd == drm_fd) {
		buf->st_mode = S_IFCHR |
			(S_IRWXG | S_IRGRP |  S_IRWXU | S_IRUSR);
		buf->st_uid = 0;
		buf->st_gid = getgid();
		return 0;
	}

	return libc_fstat(fd, buf);
}

__attribute__ ((visibility ("default"))) int
fstat64(int fd, struct stat64 *buf)
{
	if (fd == drm_fd) {
		buf->st_mode = S_IFCHR |
			(S_IRWXG | S_IRGRP |  S_IRWXU | S_IRUSR);
		buf->st_uid = 0;
		buf->st_gid = getgid();
		return 0;
	}

	return libc_fstat64(fd, buf);
}

__attribute__ ((visibility ("default"))) int
__fxstat(int ver, int fd, struct stat *buf)
{
	if (fd == drm_fd) {
		buf->st_mode = S_IFCHR |
			(S_IRWXG | S_IRGRP |  S_IRWXU | S_IRUSR);
		buf->st_rdev = makedev(DRM_MAJOR, 0);
		buf->st_uid = 0;
		buf->st_gid = getgid();
		return 0;
	}

	return libc__fxstat(ver, fd, buf);
}

__attribute__ ((visibility ("default"))) int
__fxstat64(int ver, int fd, struct stat64 *buf)
{
	if (fd == drm_fd) {
		buf->st_mode = S_IFCHR |
			(S_IRWXG | S_IRGRP |  S_IRWXU | S_IRUSR);
		buf->st_rdev = makedev(DRM_MAJOR, 0);
		buf->st_uid = 0;
		buf->st_gid = getgid();
		return 0;
	}

	return libc__fxstat64(ver, fd, buf);
}

__attribute__ ((visibility ("default"))) int
fcntl(int fd, int cmd, ...)
{
	va_list args;
	int param;

	if (fd == drm_fd && cmd == F_DUPFD_CLOEXEC)
		return drm_fd;

	va_start(args, cmd);
	param = va_arg(args, int);
	va_end(args);

	return libc_fcntl(fd, cmd, param);
}

__attribute__ ((visibility ("default"))) int
fcntl64(int fd, int cmd, ...)
{
	va_list args;
	int param;

	if (fd == drm_fd && cmd == F_DUPFD_CLOEXEC)
		return drm_fd;

	va_start(args, cmd);
	param = va_arg(args, int);
	va_end(args);

	return libc_fcntl64(fd, cmd, param);
}

__attribute__ ((visibility ("default"))) void *
mmap(void *addr, size_t len, int prot, int flags,
     int fildes, off_t off)
{
        if (fildes == drm_fd) {
                return libc_mmap(NULL, len, prot, flags | MAP_ANONYMOUS,
                                 -1, 0);
        } else {
                return libc_mmap(addr, len, prot, flags, fildes, off);
        }
}

__attribute__ ((visibility ("default"))) void *
mmap64(void *addr, size_t len, int prot, int flags,
       int fildes, off_t off)
{
        if (fildes == drm_fd) {
                return libc_mmap64(NULL, len, prot, flags | MAP_ANONYMOUS,
                                   -1, 0);
        } else {
                return libc_mmap64(addr, len, prot, flags, fildes, off);
        }
}


__attribute__ ((visibility ("default"))) ssize_t
readlink(const char *pathname, char *buf, size_t bufsiz)
{
	if (strcmp(pathname, SYSFS_PATH) == 0)
		return snprintf(buf, bufsiz, "../../../bus/pci");

	return libc_readlink(pathname, buf, bufsiz);
}

__attribute__ ((visibility ("default"))) int
ioctl(int fd, unsigned long request, ...)
{
	va_list args;
	void *argp;
	struct stat buf;
	char *pci_id;

	va_start(args, request);
	argp = va_arg(args, void *);
	va_end(args);

	if (_IOC_TYPE(request) == DRM_IOCTL_BASE &&
	    drm_fd != fd && libc_fstat(fd, &buf) == 0 &&
	    (buf.st_mode & S_IFMT) == S_IFCHR && major(buf.st_rdev) == DRM_MAJOR) {
		drm_fd = fd;
	}

	if (fd == drm_fd) {
		switch (request) {
                case DRM_IOCTL_VERSION:
			return dispatch_version(fd, request, argp);

		case DRM_IOCTL_I915_GETPARAM: {
			struct drm_i915_getparam *getparam = argp;

                        switch (getparam->param) {
                        case I915_PARAM_HAS_RELAXED_DELTA:
                        case I915_PARAM_HAS_WAIT_TIMEOUT:
                        case I915_PARAM_HAS_EXEC_NO_RELOC:
                        case I915_PARAM_HAS_CONTEXT_ISOLATION:
                                *getparam->value = 1;
                                break;
                        case I915_PARAM_CHIPSET_ID:
                                pci_id = getenv("INTEL_DEVID_OVERRIDE");

                                if (pci_id)
                                    *getparam->value = strtod(pci_id, NULL);
                                else
                                    return -EINVAL;

                                break;
                        case I915_PARAM_CMD_PARSER_VERSION:
                                *getparam->value = 9;
                                break;
                        case I915_PARAM_HAS_EXEC_SOFTPIN:
                                *getparam->value = 1;
                                break;
                        case I915_PARAM_HAS_ALIASING_PPGTT:
                                *getparam->value = I915_GEM_PPGTT_FULL;
                                break;
			}

                        return 0;
		}

                case DRM_IOCTL_I915_GEM_CONTEXT_GETPARAM: {
                        struct drm_i915_gem_context_param *getparam = argp;

                        switch (getparam->param) {
                        case I915_CONTEXT_PARAM_GTT_SIZE:
                                getparam->value = (1ull << 47);
                                return 0;
                        }
                        return -EINVAL;
                }


                case DRM_IOCTL_I915_GEM_GET_APERTURE: {
                        struct drm_i915_gem_get_aperture *aperture = argp;
                        aperture->aper_available_size = 128 * 1024 * 1024;
                        return 0;
                }

                case DRM_IOCTL_I915_GEM_MMAP: {
                        struct drm_i915_gem_mmap *arg = argp;
                        arg->addr_ptr = (uintptr_t)libc_mmap(
                                NULL, arg->size, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
                        return 0;
                }

                case DRM_IOCTL_I915_GEM_CONTEXT_CREATE: {
                        struct drm_i915_gem_context_create *cc = argp;
                        cc->ctx_id = 1; /* must be non-zero */
                }

                case DRM_IOCTL_SYNCOBJ_CREATE: {
                        struct drm_syncobj_create *args = argp;
                        args->handle = 1;
                }

                case DRM_IOCTL_SYNCOBJ_DESTROY:
                default:
                        return 0;
		}
	} else {
		return libc_ioctl(fd, request, argp);
	}
}

static void __attribute__ ((constructor))
init(void)
{
	libc_open = dlsym(RTLD_NEXT, "open");
	libc_open64 = dlsym(RTLD_NEXT, "open64");
	libc_close = dlsym(RTLD_NEXT, "close");
	libc_fcntl = dlsym(RTLD_NEXT, "fcntl");
	libc_fcntl64 = dlsym(RTLD_NEXT, "fcntl64");
	libc_fstat = dlsym(RTLD_NEXT, "fstat");
	libc_fstat64 = dlsym(RTLD_NEXT, "fstat64");
	libc__fxstat = dlsym(RTLD_NEXT, "__fxstat");
	libc__fxstat64 = dlsym(RTLD_NEXT, "__fxstat64");
	libc_ioctl = dlsym(RTLD_NEXT, "ioctl");
	libc_mmap = dlsym(RTLD_NEXT, "mmap");
	libc_mmap64 = dlsym(RTLD_NEXT, "mmap64");
	libc_readlink = dlsym(RTLD_NEXT, "readlink");
}
