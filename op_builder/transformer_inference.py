from .builder import CUDAOpBuilder, installed_cuda_version


class InferenceBuilder(CUDAOpBuilder):
    BUILD_VAR = "DS_BUILD_TRANSFORMER_INFERENCE"
    NAME = "transformer_inference"

    def __init__(self, name=None):
        name = self.NAME if name is None else name
        super().__init__(name=name)

    def absolute_name(self):
        return f'deepspeed.ops.transformer.inference.{self.NAME}_op'

    def is_compatible(self, verbose=True):
        try:
            import torch
        except ImportError:
            self.warning(
                "Please install torch if trying to pre-compile inference kernels")
            return False

        cuda_okay = True
        if not self.is_rocm_pytorch() and torch.cuda.is_available():
            sys_cuda_major, _ = installed_cuda_version()
            torch_cuda_major = int(torch.version.cuda.split('.')[0])
            cuda_capability = torch.cuda.get_device_properties(0).major
            if cuda_capability >= 8:
                if torch_cuda_major < 11 or sys_cuda_major < 11:
                    self.warning(
                        "On Ampere and higher architectures please use CUDA 11+")
                    cuda_okay = False
        return super().is_compatible(verbose) and cuda_okay

    def sources(self):
        return [
            'csrc/transformer/inference/csrc/pt_binding.cpp',
            'csrc/transformer/inference/csrc/gelu.cu',
            'csrc/transformer/inference/csrc/relu.cu',
            'csrc/transformer/inference/csrc/normalize.cu',
            'csrc/transformer/inference/csrc/softmax.cu',
            'csrc/transformer/inference/csrc/dequantize.cu',
            'csrc/transformer/inference/csrc/dequantize_n.cu',
            'csrc/transformer/inference/csrc/custom_gemm.cu',
            'csrc/transformer/inference/csrc/quantize.cu',
            'csrc/transformer/inference/csrc/transform.cu',
            'csrc/transformer/inference/csrc/apply_rotary_pos_emb.cu',
            'csrc/transformer/inference/csrc/swizzled_quantize.cu',
        ]

    def extra_ldflags(self):
        import deepspeed
        import os
        lib_path = os.path.join(os.path.dirname(deepspeed.__file__), 'ops/libs/cutlass')
        return [
            f'-L{lib_path}',
            '-lgemmlib',
            '-lgemmi4',
            '-lcurand',
            f'-Wl,-rpath,{lib_path}'
        ]

    def include_paths(self):
        return ['csrc/transformer/inference/includes', 'csrc/includes']
