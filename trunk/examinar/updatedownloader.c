/*  update_downloader -- downloads titles from NUS, and decrypts them. It also
            displays data about the TMD. Supports downloading alternate
            versions of the title. Supports downloading all versions of a title
            (via bruteforce). If you have a file named strip in the directory
            in which update_downloader lives, it will also remove the ELFLOADER
            header from the kernel of the IOS. Also, a file named fix will
            "fix" the system menu so it can be loaded into IDA Pro. You still
            must do the segment changing blah blah blah.

    Copyright (C) 2008 SquidMan

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "es.h"
#include "endian.h"
#include "aes.h"

#define SHOPPING_USER_AGENT		"\"Opera/9.00 (Nintendo Wii; U; ; 1038-58; Wii Shop Channel/1.0; en)\""
#define UPDATING_USER_AGENT		"\"wii libnup/1.0\""
#define VIRTUAL_CONSOLE_USER_AGENT	"\"libec-3.0.7.06111123\""
#define WIICONNECT24_USER_AGENT		"\"WiiConnect24/1.0FC4plus1 (build 061114161108)\""
#define UPDATE_USER_AGENT		UPDATING_USER_AGENT

#define VERSION_STRING			"v2.0"
// Lol, its over 9000!
#define DEFAULT_VERSION_COUNT		9001

#define PROPER_MKDIR			1

void decrypt_buffer(u16 index, u8 *source, u8 *dest, u32 len)
{
	static u8 iv[16];
	if (!source) {
		exit(1);
	}
	if (!dest) {
		exit(1);
	}

	memset(iv, 0, 16);
	memcpy(iv, &index, 2);
	aes_decrypt(iv, source, dest, len);
}

void get_title_key(signed_blob *s_tik, u8 *key)
{
	static u8 iv[16];
	static u8 keyin[16];
	static u8 keyout[16];
	static u8 commonkey[16] = COMMON_KEY;

	const tik *p_tik;
	p_tik = (tik*)SIGNATURE_PAYLOAD(s_tik);
	u8 *enc_key = (u8 *)&p_tik->cipher_title_key;
	memcpy(keyin, enc_key, sizeof keyin);
	memset(keyout, 0, sizeof keyout);
	memset(iv, 0, sizeof iv);
	memcpy(iv, &p_tik->titleid, sizeof p_tik->titleid);

	aes_set_key(commonkey);
	aes_decrypt(iv, keyin, keyout, sizeof(keyin));
	memcpy(key, keyout, sizeof keyout);
}

static void print_tmd_content(FILE* output, tmd_content content)
{
	int i;
	fprintf(output, "|----------------------------------------------------------------\n");
	fprintf(output, "| Content:\t\t\t%08x.app\n", be32(content.cid));
	fprintf(output, "| Index:\t\t\t%u\n", be16(content.index));
	if (be16(content.type) == CONTENT_TYPE_LOCAL)
		fprintf(output, "| Type:\t\t\t\tLocal\n");
	else if (be16(content.type) == CONTENT_TYPE_SHARED)
		fprintf(output, "| Type:\t\t\t\tShared\n");
	fprintf(output, "| Size:\t\t\t\t%llu\n", be64(content.size));
	fprintf(output, "| Hash:\t\t\t\t"); for ( i = 0; i < 20; i++){ fprintf(output, "%02x", content.hash[i]); } fprintf(output, "\n");
}

int get_file_from_NUS(char* filename, char* titleid)
{
	char URLToGrab[256];
	char wget_command[256];
	sprintf(URLToGrab, "http://ccs.shop.wii.com/ccs/download/%s/%s", titleid, filename);
	sprintf(wget_command, "wget %s --user-agent=%s", URLToGrab, UPDATE_USER_AGENT);
	system(wget_command);
	FILE *fp = fopen(filename, "rb");
	if (fp == NULL) {
		printf("Couldn't download file!\n");
		return 0;
	}else{
		fclose(fp);
		return 1;
	}
}

static void strip_kernel(char* kernel_path, u32 title_idl)
{
	FILE* fp = fopen(kernel_path, "rb");
	if(fp == NULL) {
		printf("Could not open kernel for reading!\nAborting Strip...\n");
		return;
	}
	fseek(fp, 0, SEEK_END);
	int kernel_offset = 0x594;
	if(title_idl < 30)
		kernel_offset = 0x334;
	int kernel_size = ftell(fp) - kernel_offset;
	u8* kernel_buf = (u8*)malloc(kernel_size);
	if(kernel_buf == NULL) { printf("Error Allocating for Kernel Buffer\nAborting Strip...\n"); fclose(fp); return; }
	fseek(fp, kernel_offset, SEEK_SET);
	fread(kernel_buf, kernel_size, 1, fp);
	fclose(fp);
	fp = fopen(kernel_path, "wb+");
	if(fp == NULL) {
		printf("Could not open kernel for writing!\nAborting Strip...\n");
		return;
	}
	fwrite(kernel_buf, kernel_size, 1, fp);
	fclose(fp);
	free(kernel_buf);
}

static void fix_sysmenu(char* executable_path)
{
	FILE* fp = fopen(executable_path, "rb");
	if(fp == NULL) {
		printf("Could not open executable for reading!\nAborting Fix...\n");
		return;
	}
	fseek(fp, 0, SEEK_END);
	int executable_size = ftell(fp);
	u8* executable_buf = (u8*)malloc(executable_size);
	if(executable_buf == NULL) { printf("Error Allocating for Executable Buffer\nAborting Fix...\n"); fclose(fp); return; }
	fseek(fp, 0, SEEK_SET);
	fread(executable_buf, executable_size, 1, fp);
	fclose(fp);
	if(executable_buf[0xe0] == 0x00)
		executable_buf[0xe0] = 0x80;
	fp = fopen(executable_path, "wb+");
	if(fp == NULL) {
		printf("Could not open executable for writing!\nAborting Fix...\n");
		return;
	}
	fwrite(executable_buf, executable_size, 1, fp);
	fclose(fp);
	free(executable_buf);
}

static void download_tmd_content(tmd_content content, u64 title_id, u16 bootindex, FILE* tmdoutput)
{
	char titleid[16];
	char src[16];
	char dst[20];
	sprintf(titleid, "%016llx", title_id);
	sprintf(src, "%08x", be32(content.cid));

	if(!get_file_from_NUS(src, titleid)) { printf("Content %s\n", src); exit(1); }

	FILE* fp = fopen(src, "rb");
	if(fp == NULL) {
		printf("Could not open file for reading!\nNow exiting...");
		exit(1);
	}
	fseek(fp, 0, SEEK_END);
	int content_size = ftell(fp);
	u8* content_buf = (u8*)malloc(content_size);
	if(content_buf == NULL) { printf("Error Allocating for Content Buffer\n"); exit(1); }
	u8* decrypted_buf = (u8*)malloc(content_size);
	if(decrypted_buf == NULL) { printf("Error Allocating for Decrypted Buffer\n"); exit(1); }
	fseek(fp, 0, SEEK_SET);
	fread(content_buf, content_size, 1, fp);
	fclose(fp);
	fp = fopen("cetk", "rb");
	if(fp == NULL) {
		printf("Could not open ticket for reading!\nNow exiting...");
		exit(1);
	}
	fseek(fp, 0, SEEK_END);
	int tiksize = ftell(fp);
	signed_blob* s_tik = (signed_blob*)malloc(tiksize);
	if(s_tik == NULL) { printf("Error Allocating for Signed Ticket\n"); exit(1); }
	fseek(fp, 0, SEEK_SET);
	fread(s_tik, tiksize, 1, fp);
	fclose(fp);
	u8 key[16];
	get_title_key(s_tik, key);
	aes_set_key(key);
	decrypt_buffer(content.index, content_buf, decrypted_buf, content_size);
	sprintf(dst, "%s.app", src);
	fp = fopen(dst, "wb+");
	if(fp == NULL) {
		printf("Could not open file for writing!\nNow exiting...");
		exit(1);
	}
	fwrite(decrypted_buf, content_size, 1, fp);
	fclose(fp);
	remove(src);
	FILE* stripfp = fopen("../strip", "rb");
	if((stripfp != NULL) && (be16(content.index) == bootindex) && (TITLE_IDH(title_id) == 0x00000001) && (TITLE_IDL(title_id) > 0x2) && (TITLE_IDL(title_id) < 0x100)) {
		fprintf(tmdoutput, "| Stripping kernel!\n");
		strip_kernel(dst, TITLE_IDL(title_id));
	}else{
		fprintf(tmdoutput, "| Not stripping");
		if(stripfp == NULL)
			fprintf(tmdoutput, " because strip was not found.\n");
		else if(be16(content.index) != bootindex)
			fprintf(tmdoutput, " because this is not the kernel.\n");
		else if((TITLE_IDH(title_id) != 0x00000001) || (TITLE_IDL(title_id) <= 0x2) || (TITLE_IDL(title_id) >= 0x100))
			fprintf(tmdoutput, " because this is not an IOS.\n");
	}
	if(stripfp != NULL)
		fclose(stripfp);

	FILE* fixfp = fopen("../fix", "rb");
	if((fixfp != NULL) && (be16(content.index) == bootindex) && (title_id == 0x0000000100000002LL)) {
		fprintf(tmdoutput, "| Fixing System Menu!\n");
		fix_sysmenu(dst);
	}else{
		fprintf(tmdoutput, "| Not fixing");
		if(fixfp == NULL)
			fprintf(tmdoutput, " because fix was not found.\n");
		else if(be16(content.index) != bootindex)
			fprintf(tmdoutput, " because this is not the executable.\n");
		else if(title_id != 0x0000000100000002LL)
			fprintf(tmdoutput, " because this is not the System Menu.\n");
	}
	if(fixfp != NULL)
		fclose(fixfp);

	free(decrypted_buf);
	free(content_buf);
	free(s_tik);
}

static void print_tmd(FILE* tmdoutput, tmd* tmd_data)
{
	int i;
	fprintf(tmdoutput, "/----------------------------------------------------------------\n");
	fprintf(tmdoutput, "| General TMD Data:                                              \n");
	fprintf(tmdoutput, "|----------------------------------------------------------------\n");
	fprintf(tmdoutput, "| Issuer:\t\t\t%s\n", tmd_data->issuer);
	fprintf(tmdoutput, "| Version:\t\t\t%u\n", tmd_data->version);
	fprintf(tmdoutput, "| CA CRL Version:\t\t%u\n", tmd_data->ca_crl_version);
	fprintf(tmdoutput, "| Signer CRL Version:\t\t%u\n", tmd_data->signer_crl_version);
	fprintf(tmdoutput, "| System Version:\t\t%llu\n", be64(tmd_data->sys_version));
	fprintf(tmdoutput, "| Title ID:\t\t\t%08x-%08x\n", (u32)(be64(tmd_data->title_id)>>32), (u32)(be64(tmd_data->title_id)));
	fprintf(tmdoutput, "| Title Type:\t\t\t%u\n", be32(tmd_data->title_type));
	fprintf(tmdoutput, "| Group ID:\t\t\t%u\n", be16(tmd_data->group_id));
	fprintf(tmdoutput, "| Region:\t\t\t%u\n", be16(tmd_data->region));
	fprintf(tmdoutput, "| Ratings:\t\t\t"); for (i = 0; i < 16; i++){ fprintf(tmdoutput, "%02x", tmd_data->ratings[i]); } fprintf(tmdoutput, "\n");
	fprintf(tmdoutput, "| Access Rights:\t\t%u\n", be32(tmd_data->access_rights));
	fprintf(tmdoutput, "| Title Version:\t\t%u\n", be16(tmd_data->title_version));
	fprintf(tmdoutput, "| Number of Contents:\t\t%u\n", be16(tmd_data->num_contents));
	fprintf(tmdoutput, "| Boot Index:\t\t\t%u\n", be16(tmd_data->boot_index));
	fprintf(tmdoutput, "\\----------------------------------------------------------------\n");
	printf("\n");
	fprintf(tmdoutput, "/----------------------------------------------------------------\n");
	fprintf(tmdoutput, "| Contents:                                                      \n");
	tmd_content* tmd_contents = TMD_CONTENTS(tmd_data);
	for (i = 0; i < be16(tmd_data->num_contents) && i < MAX_NUM_TMD_CONTENTS; i++)
	{
		print_tmd_content(tmdoutput, tmd_contents[i]);
		download_tmd_content(tmd_contents[i], be64(tmd_data->title_id), be16(tmd_data->boot_index), tmdoutput);
	}
	fprintf(tmdoutput, "\\----------------------------------------------------------------\n");
}

void download_all_versions(char* titleid, int ver_max)
{
	FILE* fp;
	FILE* logfile;
	FILE* err_log = fopen("err_log", "wb");
	char newDirectory[256];
	char tmdname[16];
	int filesize;
	tmd* tmd_data;
	int veridx = 0;
	int version = 1;
	int *versions = malloc(ver_max*sizeof(int));
	if(versions == NULL) { printf("Error Allocating for version list\n"); exit(1); }
	for(version = 1; version < ver_max; version++) {
		sprintf(tmdname, "tmd.%d", version);
		get_file_from_NUS(tmdname, titleid);
		fp = fopen(tmdname, "rb");
		if(fp != NULL) {
			versions[veridx++] = version;
			remove(tmdname);
		}
	}
	fwrite(&veridx, sizeof(int), 1, err_log);
	fwrite(versions, sizeof(int), veridx, err_log);
	for(veridx--; veridx >= 0; veridx--) {
		version = versions[veridx];
		sprintf(newDirectory, "%s.%d", titleid, version);
#ifdef PROPER_MKDIR
		mkdir(newDirectory, S_IRWXU);
#else
		mkdir(newDirectory);
#endif
		chdir(newDirectory);
		sprintf(tmdname, "tmd.%d", version);
		if(!get_file_from_NUS(tmdname, titleid)) { printf("TMD with version %d\n", version); continue; }
		if(!get_file_from_NUS("cetk", titleid)) { printf("cetk\n"); continue; }

		fp = fopen(tmdname, "rb");
		if (fp == NULL) {
			fprintf(err_log, "Couldn't open TMD for version %d!\n", version);
			continue;
		}
		fseek(fp, 0, SEEK_END);
		filesize = ftell(fp);
		tmd_data = (tmd*)calloc(filesize, 1);
		if(tmd_data == NULL) { printf("Error Allocating for TMD Data\n"); exit(1); }

		fseek(fp, 0, SEEK_SET);
		fread(tmd_data, filesize, 1, fp);

		logfile = fopen("downloadlog.txt", "wb+");
		if(logfile == NULL) {
			printf("Couldn't open logfile. Switching to stderr!\n");
			logfile = stderr;
		}

		print_tmd(logfile, SIGNATURE_PAYLOAD(tmd_data));
		free(tmd_data);
		fclose(fp);
		chdir("../");
	}
	exit(0);
}

void bad_params(char* argv[])
{
	printf("Incorrect parameters. Use update_downloader like so:\n\t%s \"titleid\" [version]\n", argv[0]);
	exit(1);
}

int main(int argc, char* argv[])
{
	printf("Update Downloader %s (c) 2008 Alex Marshall (SquidMan)\n\n", VERSION_STRING);
	if (argc != 2 && argc != 3 && argc != 4)
		bad_params(argv);
	char newDirectory[22];
	strcpy(newDirectory, argv[1]);
	if(argc >= 3){
		if(strcmp(argv[2], "all") != 0){ strcat(newDirectory, "."); strcat(newDirectory, argv[2]); }
		else if(argc >= 4)
			download_all_versions(argv[1], atoi(argv[3]));
		else
			download_all_versions(argv[1], DEFAULT_VERSION_COUNT);
	}
#ifdef PROPER_MKDIR
	mkdir(newDirectory, S_IRWXU);
#else
	mkdir(newDirectory);
#endif
	chdir(newDirectory);
	char tmdname[16];
	sprintf(tmdname, "tmd");
	if(argc >= 3){ strcat(tmdname, "."); strcat(tmdname, argv[2]); }

	if(!get_file_from_NUS(tmdname, argv[1])) { printf("TMD\n"); exit(1); }
	if(!get_file_from_NUS("cetk", argv[1])) { printf("cetk\n"); exit(1); }

	FILE *fp = fopen(tmdname, "rb");
	if (fp == NULL) {
		printf("Couldn't open TMD!\n");
		exit(1);
	}
	fseek(fp, 0, SEEK_END);
	int filesize = ftell(fp);
	tmd* tmd_data = (tmd*)calloc(filesize, 1);
	if(tmd_data == NULL) { printf("Error Allocating for TMD Data\n"); exit(1); }
	fseek(fp, 0, SEEK_SET);
	fread(tmd_data, filesize, 1, fp);

	FILE* logfile = fopen("downloadlog.txt", "wb+");
	if(logfile == NULL) {
		printf("Couldn't open logfile. Switching to stderr!\n");
		logfile = stderr;
	}
	print_tmd(logfile, SIGNATURE_PAYLOAD(tmd_data));
	free(tmd_data);
	fclose(fp);
	return 0;
}

