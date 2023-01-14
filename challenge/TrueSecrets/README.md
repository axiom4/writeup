# Analyzing memory with volatility3

```
# vol -f ../TrueSecrets.raw windows.cmdline.CmdLine

Volatility 3 Framework 2.4.0
Progress:  100.00		PDB scanning finished
PID	Process	Args

4	System	Required memory at 0x10 is not valid (process exited?)
252	smss.exe	\SystemRoot\System32\smss.exe
320	csrss.exe	%SystemRoot%\system32\csrss.exe ObjectDirectory=\Windows SharedSection=1024,12288,512 Windows=On SubSystemType=Windows ServerDll=basesrv,1 ServerDll=winsrv:UserServerDllInitialization,3 ServerDll=winsrv:ConServerDllInitialization,2 ServerDll=sxssrv,4 ProfileControl=Off MaxRequestThreads=16
...
2128	TrueCrypt.exe	"C:\Program Files\TrueCrypt\TrueCrypt.exe"
...
2176	7zFM.exe	"C:\Program Files\7-Zip\7zFM.exe" "C:\Users\IEUser\Documents\backup_development.zip"
...

```

# Dump PID 2176 files


```
# vol -f ../TrueSecrets.raw windows.dumpfiles.DumpFiles --pid 2176
Volatility 3 Framework 2.4.0
Progress:  100.00		PDB scanning finished	Cache	FileObject	FileName	Result

DataSectionObject	0x8392eb08	StaticCache.dat	Error dumping file
SharedCacheMap	0x8392eb08	StaticCache.dat	
file.0x8392eb08.0x844ef008.SharedCacheMap.StaticCache.dat.vacb
DataSectionObject	0x843f6158	backup_development.zip	file.0x843f6158.0x839339d0.DataSectionObject.backup_development.zip.dat
SharedCacheMap	0x843f6158	backup_development.zip	file.0x843f6158.0x9185db40.SharedCacheMap.backup_development.zip.vacb
ImageSectionObject	0x84457288	comctl32.dll	file.0x84457288.0x8445a568.ImageSectionObject.comctl32.dll.img
ImageSectionObject	0x838afd38	7zFM.exe	
...
```

# Extract zip file

```
# unzip file.0x843f6158.0x839339d0.DataSectionObject.backup_development.zip.dat
Archive:  file.0x843f6158.0x839339d0.DataSectionObject.backup_development.zip.dat
 extracting: development.tc

```

# Find truecrypt memory password

```
# ./volatility_2.6  -f ../TrueSecrets.raw --profile=Win7SP1x86 truecryptsummary
Volatility Foundation Volatility Framework 2.6
Password             X2Hk2XbEJqWYsh8VdbSYg6WpG9g7 at offset 0x89ebf064
Process              TrueCrypt.exe at 0x91892030 pid 2128
Service              truecrypt state SERVICE_RUNNING
Kernel Module        truecrypt.sys at 0x89e8b000 - 0x89ec2000
Symbolic Link        D: -> \Device\TrueCryptVolumeD mounted 2022-12-14 21:33:00 UTC+0000
Symbolic Link        Volume{d22d7a9d-7b72-11ed-b81d-0800273bf313} -> \Device\TrueCryptVolumeD mounted 2022-12-14 21:10:21 UTC+0000
Symbolic Link        D: -> \Device\TrueCryptVolumeD mounted 2022-12-14 21:33:00 UTC+0000
Driver               \Driver\truecrypt at 0xbe6b780 range 0x89e8b000 - 0x89ec1b80
Device               TrueCryptVolumeD at 0x8391b9b0 type FILE_DEVICE_DISK
Container            Path: \??\C:\Users\IEUser\Documents\development.tc
Device               TrueCrypt at 0x83e6b600 type FILE_DEVICE_UNKNOWN
```

# Mount truecrypt volume

```
# sudo cryptsetup --type tcrypt open development.tc development
Insert passphrase for development.tc:

# sudo mount /dev/mapper/development /mnt

# cd /mnt/malware_agent

# ls
AgentServer.cs*  sessions/

```

# find encryption data

```
# cat AgentServer.cs
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Security.Cryptography;

class AgentServer {

    static void Main(String[] args)
    {
        var localPort = 40001;
        IPAddress localAddress = IPAddress.Any;
        TcpListener listener = new TcpListener(localAddress, localPort);
        listener.Start();
        Console.WriteLine("Waiting for remote connection from remote agents (infected machines)...");

        TcpClient client = listener.AcceptTcpClient();
        Console.WriteLine("Received remote connection");
        NetworkStream cStream = client.GetStream();

        string sessionID = Guid.NewGuid().ToString();

        while (true)
        {
            string cmd = Console.ReadLine();
            byte[] cmdBytes = Encoding.UTF8.GetBytes(cmd);
            cStream.Write(cmdBytes, 0, cmdBytes.Length);

            byte[] buffer = new byte[client.ReceiveBufferSize];
            int bytesRead = cStream.Read(buffer, 0, client.ReceiveBufferSize);
            string cmdOut = Encoding.ASCII.GetString(buffer, 0, bytesRead);

            string sessionFile = sessionID + ".log.enc";
            File.AppendAllText(@"sessions\" + sessionFile,
                Encrypt(
                    "Cmd: " + cmd + Environment.NewLine + cmdOut
                ) + Environment.NewLine
            );
        }
    }

    private static string Encrypt(string pt)
    {
        string key = "AKaPdSgV";
        string iv = "QeThWmYq";
        byte[] keyBytes = Encoding.UTF8.GetBytes(key);
        byte[] ivBytes = Encoding.UTF8.GetBytes(iv);
        byte[] inputBytes = System.Text.Encoding.UTF8.GetBytes(pt);

        using (DESCryptoServiceProvider dsp = new DESCryptoServiceProvider())
        {
            var mstr = new MemoryStream();
            var crystr = new CryptoStream(mstr, dsp.CreateEncryptor(keyBytes, ivBytes), CryptoStreamMode.Write);
            crystr.Write(inputBytes, 0, inputBytes.Length);
            crystr.FlushFinalBlock();
            return Convert.ToBase64String(mstr.ToArray());
        }
    }
}

```

# View logs

```
# cat *enc

wENDQtzYcL3CKv0lnnJ4hk0JYvJVBMwTj7a4Plq8h68=
M35jHmvkY9WGlWdXo0ByOJrYhHmtC8O0rZ28CviPexkfHCFTfKUQVw==
....

```

# Decrypt logs

```

# echo -n "AKaPdSgV" | xxd -ps
414b615064536756

# echo -n "QeThWmYq" | xxd -ps
51655468576d5971

# echo "wENDQtzYcL3CKv0lnnJ4hk0JYvJVBMwTj7a4Plq8h68=" | openssl enc -d -des-cbc -K 414b615064536756 -iv 51655468576d5971  -a
Cmd: hostname
DESKTOP-MRL1A9O


# for line in $(cat *.enc); do echo $line | openssl enc -d -des-cbc -K 414b615064536756 -iv 51655468576d5971  -a; done

HTB{*********}

```
