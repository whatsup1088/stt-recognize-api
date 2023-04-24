    var Recorder = function(stream) {
        var sampleBits = 16, //输出采样数位 8, 16
            sampleRate = 16000, //8000;//输出采样率
            context = new AudioContext(),
            audioInput = context.createMediaStreamSource(stream),
            recorder = context.createScriptProcessor(4096, 1, 1),
            audioData = {
                size: 0,          //录音文件长度
                buffer: [],    //录音缓存
                inputSampleRate: context.sampleRate,    //输入采样率
                inputSampleBits: 16,      //输入采样数位 8, 16
                outputSampleRate: sampleRate,
                oututSampleBits: sampleBits,
                clear: function() {
                    this.buffer = [];
                    this.size = 0;
                },
                input: function (data) {
                    this.buffer.push(new Float32Array(data));
                    this.size += data.length;
                },
                compress: function () { //合并压缩
                    //合并
                    var data = new Float32Array(this.size),
                        offset = 0;

                    for (var i = 0; i < this.buffer.length; i++) {
                        data.set(this.buffer[i], offset);
                        offset += this.buffer[i].length;
                    }

                    //压缩
                    var compression = parseInt(this.inputSampleRate / this.outputSampleRate),
                        length = data.length / compression,
                        result = new Float32Array(length),
                        index = 0, j = 0;

                    while (index < length) {
                        result[index] = data[j];
                        j += compression;
                        index++;
                    }

                    return result;
                },
                encodePCM: function(){//这里不对采集到的数据进行其他格式处理，如有需要均交给服务器端处理。
                    var sampleRate = Math.min(this.inputSampleRate, this.outputSampleRate),
                        sampleBits = Math.min(this.inputSampleBits, this.oututSampleBits),
                        bytes = this.compress(),
                        dataLength = bytes.length * (sampleBits / 8),
                        buffer = new ArrayBuffer(dataLength),
                        data = new DataView(buffer);

                    var offset = 0;
                    for (var i = 0; i < bytes.length; i++, offset += 2) {
                        var s = Math.max(-1, Math.min(1, bytes[i]));
                        data.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                    }

                    return new Blob([data]);
                }
        };

        this.start = function () {
            audioInput.connect(recorder);
            recorder.connect(context.destination);
        }

        this.stop = function () {
            recorder.disconnect();
        }

        this.getBlob = function () {
            return audioData.encodePCM();
        }

        this.clear = function() {
            audioData.clear();
        }

        recorder.onaudioprocess = function (e) {
            audioData.input(e.inputBuffer.getChannelData(0));
        }
    };
