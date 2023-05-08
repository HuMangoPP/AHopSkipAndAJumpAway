import moderngl as mgl
import numpy as np
import pygame as pg
import glm, os

FOV = 50
NEAR = 0.1
FAR = 100

class GraphicsEngine:
    def __init__(self, ctx: mgl.Context, res: tuple[int, int]):
        self.ctx = ctx
        self.res = res

        # mvp
        self.m_proj = glm.perspective(glm.radians(FOV), self.res[0]/self.res[1], NEAR, FAR)
        self.m_view = glm.lookAt(glm.vec3(0, 0, 1), glm.vec3(0), glm.vec3(0, 1, 0))

        # shader programs
        self.programs : dict[str, mgl.Program] = {}
        self.load_all_shaders()
        # self.programs['default'] = self.get_program('default')
        # self.programs['circle'] = self.get_program('circle')

        # vertex buffer objects
        self.vbo = self.get_vbo()

        # vertex array objects
        self.vaos = {}
        self.get_all_vaos()

        self.texture = None

    def get_vbo(self) -> mgl.Buffer:
        vertex_data = self.get_vertex_data()
        vbo = self.ctx.buffer(vertex_data)
        return vbo
    
    def get_vertex_data(self) -> 'np.ndarray[np.float32]':
        vertices = [(-1, 1), (1, 1), (1, -1), (-1, -1)]
        tex_vert = [(0, 0), (1, 0), (1, 1), (0, 1)]
        indices = [(0, 1, 2), (0, 2, 3)]

        vertex_data = np.hstack([self.get_data(vertices, indices), 
                                 self.get_data(tex_vert, indices)])
        return np.hstack(vertex_data)
    
    @staticmethod
    def get_data(vertices: list[tuple[float, float]], indices: 
                 list[tuple[float, float, float]]) -> 'np.ndarray[np.float32]':
        data = [vertices[ind] for triangle in indices for ind in triangle]
        return np.array(data, dtype='f4')

    def load_all_shaders(self, path='./src/pymgl/shaders'):
        shaders = os.listdir(path)
        for shader in shaders:
            shader_name = shader.split('.')
            if shader_name[1] == 'vert':
                self.programs[shader_name[0]] = self.get_program(shader_name[0])

    def get_program(self, shader_name: str) -> mgl.Program:
        with open(f'./src/pymgl/shaders/{shader_name}.vert') as file:
            vertex_shader = file.read()
        with open(f'./src/pymgl/shaders/{shader_name}.frag') as file:
            frag_shader = file.read()

        program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=frag_shader)
        program['res'].write(glm.vec2(self.res[0], self.res[1]))
        m_model = glm.mat4()

        # translate
        pos = (0, 0, 0)
        m_model = glm.translate(m_model, pos)

        # scale
        scale = (1, 1, 1)
        m_model = m_model * glm.scale(scale)

        # write
        program['m_model'].write(m_model)

        return program

    def get_all_vaos(self):
        for program_name in self.programs:
            self.vaos[program_name] = self.get_vao(self.programs[program_name], self.vbo)

    def get_vao(self, program: mgl.Program, vbo: mgl.Buffer):
        return self.ctx.vertex_array(program, [(vbo, '2f 2f', 'vertcoord', 'texcoord')])
    
    def update_texture(self, surf_size: tuple[int, int], surf: pg.Surface):
        # if self.texture:
        #     self.texture.release()
        # self.texture = self.ctx.texture(size=surf_size, components=4)
        # self.texture.repeat_x = False
        # self.texture.repeat_y = False
        # self.texture.filter = (mgl.NEAREST, mgl.NEAREST)
        # self.texture.swizzle = 'BGRA'
        if not self.texture:
            self.texture = self.ctx.texture(size=surf_size, components=4)
            self.texture.repeat_x = False
            self.texture.repeat_y = False
            self.texture.filter = (mgl.NEAREST, mgl.NEAREST)
            self.texture.swizzle = 'BGRA'
        self.texture.write(surf.get_view('1'))
        self.texture.use()
    
    def write_program_data(self, shader: str, render_data: dict[str, any]):
        for key in render_data:
            self.programs[shader][key].write(render_data[key])

    def write_model_data(self, shader: str, rect: pg.Rect):
        width, height = self.res
        m_model = glm.mat4()

        # translate
        pos = (rect.centerx/width*2-1, -(rect.centery/height*2-1), 0)
        m_model = glm.translate(m_model, pos)

        # scale
        scale = (rect.width/width, rect.height/height, 1)
        m_model = m_model * glm.scale(scale)

        # write
        self.programs[shader]['m_model'].write(m_model)

    def render(self, surf: pg.Surface, rect: pg.Surface, render_data: dict[str, any]={}, shader: str='default'):
        surf_size = surf.get_size()
        self.update_texture(surf_size, surf)
        self.programs[shader]['tex'] = 0
        # self.write_model_data(shader, rect)
        # self.write_program_data(shader, render_data)
        vao = self.vaos[shader]
        vao.render()

    def destroy(self):
        self.texture.release()
        self.vbo.release()
        [program.release() for program in self.programs.values()]