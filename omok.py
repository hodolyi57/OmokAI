import pygame
import sys
import random
import time
from pygame.locals import *

black = (0, 0, 0)
white = (255, 255, 255)
blue = (0, 50, 255)

window_width = 800
window_height = 600
board_width = 501
grid_size = 30
bg_colour = (200, 200, 200)

fps = 60
fps_clock = pygame.time.Clock()

# 초기 player_num은 0으로 함 (게임 시작전 상태인지 판별)
player_num = 0
# 시뮬레이션 최종 단계에 플레이어와 AI중 누가 수를 두는지 확인하기 위함 (테스트용)
depth_endgame = 0
# 현재 진행중인 depth 확인용
depth_current = 0
# 한 턴의 제한을 몇 초로 할지 지정
time_preset = 15.0
# 기준 시간 측정
time_std = 0.0

board_size = 19
empty = 0
player = 1
ai = 2
tie = 100

class Rule(object):
    def __init__(self, board):
        self.board = board



    # 규격 외의 수 금지
    def is_invalid(self, x, y):
        return (x < 0 or x >= board_size or y < 0 or y >= board_size)

    # 게임 오버 체크
    def is_gameover(self, x, y, stone):
        x1, y1 = x, y
        check_x = [-1, 1, -1, 1, 0, 0, 1, -1]
        check_y = [0, 0, -1, 1, -1, 1, -1, 1]
        for i in range(0, len(check_x), 2):
            cnt = 1
            for j in range(i, i + 2):
                dx, dy = check_x[j], check_y[j]
                x, y = x1, y1
                while True:
                    x, y = x + dx, y + dy
                    if self.is_invalid(x, y) or self.board[x][y] != stone:
                        break;
                    else:
                        cnt += 1
            if cnt >= 5:
                return cnt
        return cnt


def main():
    pygame.init()
    surface = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("2016320119")
    surface.fill(bg_colour)

    omok = Omok(surface)
    menu = Menu(surface)
    while True:
        run_game(surface, omok, menu)
        menu.is_continue(omok)


def run_game(surface, omok, menu):
    omok.init_game()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                menu.terminate()
            elif event.type == MOUSEBUTTONUP:
                # 오목판이 비어 있으면서 start를 누를시 초기화
                # 그게 아닐시에 오목알 배치
                if not omok.click_board(event.pos):
                    if menu.check_rect(event.pos, omok):
                        omok.init_game()
                        global player_num
                        player_num = 0
        if omok.is_gameover:
            return

        omok.check_gameover(0.1, 1)
        pygame.display.update()
        fps_clock.tick(fps)


# node 클래스 정의
class Node:
    def __init__(self):
        self.h_value = 0
        self.child = list()
        self.child_backup = list()

# 메인이 되는 오목 클래스
class Omok(object):
    def __init__(self, surface):
        self.board = [[0 for i in range(board_size)] for j in range(board_size)]
        self.menu = Menu(surface)
        self.rule = Rule(self.board)
        self.surface = surface
        self.pixel_coords = []
        self.recent_stone = []
        self.set_coords()
        self.set_image_font()
        self.start = 0
        self.stone_cnt = 0
        self.is_show = True

    def init_game(self):
        self.menu.bw = self.menu.make_text(self.menu.font, 'Black or White', blue, None, 50, window_width-160)
        self.menu.black_rect = self.menu.make_text(self.menu.font, 'Black', white, black, 80, window_width - 160)
        self.menu.white_rect = self.menu.make_text(self.menu.font, 'White', black, white, 110, window_width - 160)
        self.c_node = Node()
        self.c_node.currentboard = self.board
        self.turn = 0
        self.draw_board()
        self.menu.show_msg(empty)
        self.init_board()
        self.redos = []
        self.is_gameover = False

    def set_image_font(self):
        black_img = pygame.image.load('image/black.png')
        white_img = pygame.image.load('image/white.png')
        self.board_img = pygame.image.load('image/board.png')
        self.font = pygame.font.Font("freesansbold.ttf", 14)
        self.black_img = pygame.transform.scale(black_img, (grid_size, grid_size))
        self.white_img = pygame.transform.scale(white_img, (grid_size, grid_size))

    def init_board(self):
        for y in range(board_size):
            for x in range(board_size):
                self.board[x][y] = 0

    def draw_board(self):
        self.surface.blit(self.board_img, (0, 0))

    def draw_image(self, img_index, x, y):
        img = [self.black_img, self.white_img]
        self.surface.blit(img[img_index], (x, y))

    # 오목알을 화면에 그려주는 함수
    # 플레이어가 선공인지 후공인지 체크하여 다르게 처리
    def draw_stone(self, coord, turn, colour):
        x, y = self.get_point(coord)
        if turn == 1:
            self.board[x][y] = colour
            self.draw_image((colour-1), coord[0], coord[1])
        elif turn == 2:
            self.board[x][y] = 3 - colour
            self.draw_image((colour-1), coord[0], coord[1])
        self.stone_cnt = self.stone_cnt + 1

# 오목칸 픽셀 좌표 계산
    def set_coords(self):
        for y in range(board_size):
            for x in range(board_size):
                self.pixel_coords.append((x * grid_size + 25, y * grid_size + 25))

# 마우스 클릭시 좌표와 일치하는 칸 찾기
    def get_coord(self, pos):
        for coord in self.pixel_coords:
            x, y = coord
            rect = pygame.Rect(x, y, grid_size, grid_size)
            if rect.collidepoint(pos):
                return coord
        return None

    # 오목칸의 x,y번호 찾기
    def get_point(self, coord):
        x, y = coord
        x = (x - 25) // grid_size
        y = (y - 25) // grid_size
        return x, y

    # 각 플레이어들이 가장 최근에 둔 수의 상황 저장 (현재 설정 값 4)
    def get_recent(self, stone_xy):
        self.recent_stone.append(stone_xy)
        if len(self.recent_stone) > 4:
            del self.recent_stone[0]

    # 오목판 클릭시 내 턴 + AI 턴 진행
    def click_board(self, pos):
        global time_std
        if not player_num == 0:
            coord = self.get_coord(pos)
            if not coord:
                return False
            player_xy = self.get_point(coord)
            if self.board[player_xy[0]][player_xy[1]] != empty:
                return True
            self.draw_stone(coord, self.turn, self.turn)
            self.get_recent(player_xy)
            if self.check_gameover(coord, 1):
                 self.is_gameover = True
                 return True
            pygame.display.update()
            fps_clock.tick(fps)
            # AI턴 진행
            ai_xy = self.ai_action(self.c_node, self.board, player_num+1)
            ai_coord = ((ai_xy[0]*grid_size+25), (ai_xy[1]*grid_size+25))
            self.draw_stone(ai_coord, self.turn, 3 - self.turn)
            self.get_recent(ai_xy)
            if self.check_gameover(ai_coord, 2):
                 self.is_gameover = True
            time_std = time.time()
            return True

    def check_gameover(self, coord, player_num):
        global time_std
        # 시간 초과시 게임 오버
        if coord == 0.1:
            if time_std != 0 and time.time() - time_std > time_preset:
                    self.show_winner_msg(2)
                    self.is_gameover = True
                    return True
        else:
            x, y = self.get_point(coord)
            # 더이상 놓을 자리가 없으면 게임 오버
            if self.stone_cnt >= board_size * board_size:
                self.show_winner_msg(player_num)
                return True
            elif 5 <= self.rule.is_gameover(x, y, player_num):
                self.show_winner_msg(player_num)
                return True
            return False

    def show_winner_msg(self, player_num):
        for i in range(3):
            self.menu.show_msg(player_num)
            pygame.display.update()
            pygame.time.delay(200)
            self.menu.show_msg(player_num)
            pygame.display.update()
            pygame.time.delay(200)
        self.menu.show_msg(player_num)

    # AI가 어떻게 수를 놓을지 정의

    #iterative deepening search


    # =======================================================
    # AI 부분 정의
    # 플레이어가 흑, AI가 백을 기준으로 작성.
    # 때문에 board에는 플레이어 기준 선후공 관계없이 player_num = 1이 저장되도록 함.
    # =======================================================
    # 최종적으로 AI가 돌을 놓을 좌표를 return
    def ai_action(self, c_node, board, player_turn):
        global time_std
        time_std = time.time()
        x = 0
        y = 0
        # 최대 depth 설정
        depth_max = 3
        # depth가 1일 때부터 iterative-deepening-search 방식으로 alpha-beta-search 실행
        x, y = self.alpha_beta_search(c_node, board, depth_max, player_turn)
        return x, y




    # alpha-beta-search
    def alpha_beta_search(self, c_node, board, depth_max, player_turn):
        # 시간 제한 동안 depth를 1씩 증가시키며 search 실행
        for depth in range(1, depth_max+1):
            global depth_endgame  # 이 요소를 도입하는 것이 효율적인지는 검증 필요
            global depth_current
            depth_current = depth
            depth_endgame = (depth % 2) + 1
            # alpha와 beta의 초기값이 각각 음의 무한대와 양의 무한대
            alpha = float("-inf")
            beta = float("+inf")
            value_tmp = self.alpha_beta_pruning(c_node, depth, player_turn, alpha, beta)
            # 만약 현재 depth를 탐색중 시간이 만료시, 그 전 단계의 depth로 탐색한 결과 반환
            if value_tmp == 0.1:
                break
            else:
                # h_value 확정
                c_node.h_value = value_tmp
                # 현재 child 노드 백업
                c_node.child_backup = c_node.child
                # 더 이상 depth를 증가시킬 필요 없이 명확할 때, 이 값으로 확정함.
                if c_node.h_value >= 99999999:
                    c_node.child = list()
                    break
            # child 노드 초기화
            c_node.child = list()
        x_tmp = 0
        y_tmp = 0
        for i in c_node.child_backup:
            if c_node.h_value == i.h_value:
                x_tmp = i.x_tmp
                y_tmp = i.y_tmp
        board[x_tmp][y_tmp] = player_turn

        return x_tmp, y_tmp





    # alpha-beta pruning 알고리즘
    # 컴퓨터가 2
    def alpha_beta_pruning(self, node, depth, player_check, alpha, beta):
        # 자식 노드 생성 완료일 때 heuristic value 반환
        # 속도 향상을 위해 직전 놓인 돌 4개 주변 5칸을 벗어난 수를 두는 child node는 생성하지 않음
        if depth == 0:
            return self.Heuristic(node.currentboard)
        if player_check == 1:
            for x in range(0, 19):
                for y in range(0, 19):
                    if node.currentboard[x][y] == 0:
                        childnode = Node()
                        childnode.currentboard = list()
                        for i in range(0, 19):
                            tmp_og = list()
                            for j in range(0, 19):
                                if node.currentboard[i][j] == 0:
                                    tmp_og.append(0)
                                elif node.currentboard[i][j] == 1:
                                    tmp_og.append(1)
                                elif node.currentboard[i][j] == 2:
                                    tmp_og.append(2)
                            childnode.currentboard.append(tmp_og)
                        childnode.currentboard[x][y] = player_check
                        childnode.x_tmp = x
                        childnode.y_tmp = y
                        node.child.append(childnode)
                    else:
                        pass
            h_value = float("inf")
            for i in node.child:
                i.h_value = self.alpha_beta_pruning(i, depth - 1, 2, alpha, beta)
                # 시간 만료시 0.1 return
                if i.h_value == 0.1:
                    return 0.1
                h_value = min(h_value, i.h_value)
                beta = min(beta, h_value)
                if beta <= alpha:
                    break
            # 시간초과시 0.1 return
            if (time.time() - time_std) > time_preset:
                return 0.1
            else:
                return h_value
        elif player_check == 2:
            for x in range(0, 19):
                for y in range(0, 19):
                    if node.currentboard[x][y] == 0:
                        for tmp in self.recent_stone:
                            # 주변 5x5칸만 탐색
                            if x >= (tmp[0] - 2) and x <= (tmp[0]+2) and y >= (tmp[1] - 2) and y <= (tmp[1] + 2):
                                childnode = Node()
                                childnode.currentboard = list()
                                for i in range(0, 19):
                                    # 기존 오목판을 tmp_og에 복사후에 childnode에 옮김
                                    tmp_og = list()
                                    for j in range(0, 19):
                                        if node.currentboard[i][j] == 0:
                                            tmp_og.append(0)
                                        elif node.currentboard[i][j] == 1:
                                            tmp_og.append(1)
                                        elif node.currentboard[i][j] == 2:
                                            tmp_og.append(2)
                                    childnode.currentboard.append(tmp_og)
                                # 자식 노드를 생성
                                childnode.currentboard[x][y] = player_check
                                childnode.x_tmp = x
                                childnode.y_tmp = y
                                node.child.append(childnode)
                                break
                    else:
                                pass
            h_value = float("-inf")
            for i in node.child:
                i.h_value = self.alpha_beta_pruning(i, depth - 1, 1, alpha, beta)
                # 시간 만료시 0.1 return
                if i.h_value == 0.1:
                    return 0.1
                h_value = max(h_value, i.h_value)
                alpha = max(alpha, h_value)
                if beta <= alpha:
                    break
            # 시간 만료시 0.1 return
            if (time.time() - time_std) > time_preset:
                return 0.1
            else:
                return h_value


    # 여러 경우의 수에 대해 heuristic function을 적용하여 그 값을 계산
    # 확실한 승리가 결정되면 무조건 그 수를 두도록 함. ex) AI가 5를 만들수있는 경우
    # 마찬가지로 확실한 패배가 결정되는 수는 두지 않도록 함.
    # depth가 홀수면 시뮬레이션상에서 마지막 수가 AI의 수, 짝수면 플레이어의 수
    def Heuristic(self, board):
        h_value = 0

        # 기본적으로 근처에 많은 돌이 있을 때 가산점
        for x in range(1, 18):
            for y in range(1, 18):
                if (board[x][y] == 0):
                    pass
                else:
                    if (board[x - 1][y - 1] == 2):
                        h_value = h_value + 1
                    if (board[x][y - 1] == 2):
                        h_value = h_value + 1
                    if (board[x + 1][y - 1] == 2):
                        h_value = h_value + 1
                    if (board[x - 1][y] == 2):
                        h_value = h_value + 1
                    if (board[x + 1][y] == 2):
                        h_value = h_value + 1
                    if (board[x - 1][y + 1] == 2):
                        h_value = h_value + 1
                    if (board[x][y + 1] == 2):
                        h_value = h_value + 1
                    if (board[x + 1][y + 1] == 2):
                        h_value = h_value + 1

        for x in range(0, 15):
            for y in range(0, 15):
                # 3-3은 금지!!
                # value 배점 같은 경우 양쪽이 열린 3을 비중있게 매김.
                # 우선 depth 1일 때, 확실하게 AI가 이기는 경우는 확정
                if depth_current == 1:  # 현재 depth 1일 때 알고리즘 실행중이면 적용
                    # AI가 가로 5칸 만드는 경우
                    if y == 14:
                        for tmp_y in range(15, 19):
                            if board[x][tmp_y] == 2 and board[x + 1][tmp_y] == 2 and board[x + 2][tmp_y] == 2 and board[x + 3][tmp_y] == 2:
                                if board[x + 4][tmp_y] == 2:
                                    h_value = 99999999
                                    return h_value  # 확정
                    if board[x][y] == 2 and board[x+1][y] == 2 and board[x+2][y] == 2 and board[x+3][y] == 2:
                        if board[x+4][y] == 2:
                            h_value = 99999999
                            return h_value  # 확정
                    # AI가 세로 5칸 만드는 경우
                    if x == 14:
                        for tmp_x in range(15, 19):
                            if board[tmp_x][y] == 2 and board[tmp_x][y + 1] == 2 and board[tmp_x][y + 2] == 2 and board[tmp_x][
                                y + 3] == 2:
                                if board[tmp_x][y + 4] == 2:
                                    h_value = 99999999
                                    return h_value
                    if board[x][y] == 2 and board[x][y+1] == 2 and board[x][y+2] == 2 and board[x][y+3] == 2:
                        if board[x][y+4] == 2:
                            h_value = 99999999
                            return h_value
                    # AI가 / 방향 대각선 5칸 만드는 경우
                    if board[x+4][y] == 2 and board[x+3][y+1] == 2 and board[x+2][y+2] == 2 and board[x+1][y+3] == 2:
                        if board[x][y+4] == 2:
                            h_value = 99999999
                            return h_value
                    # AI가 반대 방향 대각선 5칸 만드는 경우
                    if board[x][y] == 2 and board[x+1][y+1] == 2 and board[x+2][y+2] == 2 and board[x+3][y+3] == 2:
                        if board[x+4][y+4] == 2:
                            h_value = 99999999
                            return h_value

                    # 이제 위 경우에 해당 안 되고, 플레이어가 반틈 열린 4를 만들었는지 확인
                    # 만들었다면 그 곳을 내버려두는 수는 제외, 반드시 막도록 함.
                    # 플레이어가 가로 4 만드는 경우 + 오른쪽이 열려있는 경우
                    if y == 14:
                        for tmp_y in range(15, 19):
                            if board[x][tmp_y] == 1 and board[x + 1][tmp_y] == 1 and board[x + 2][tmp_y] == 1 and board[x + 3][
                                tmp_y] == 1:
                                if board[x + 4][tmp_y] == 0:
                                    h_value = 0 - 99999999
                                    return h_value
                    if board[x][y] == 1 and board[x+1][y] == 1 and board[x+2][y] == 1 and board[x+3][y] == 1:
                        if board[x+4][y] == 0:
                            h_value = 0 - 99999999
                            return h_value
                    # 플레이어가 가로 4 만드는 경우 + 왼쪽이 열려있는 경우
                    if y == 14:
                        for tmp_y in range(15, 19):
                            if board[x + 1][tmp_y] == 1 and board[x + 2][tmp_y] == 1 and board[x + 3][tmp_y] == 1 and board[x + 4][
                                tmp_y] == 1:
                                if board[x][tmp_y] == 0:
                                    h_value = 0 - 99999999
                                    return h_value
                    if board[x+1][y] == 1 and board[x+2][y] == 1 and board[x+3][y] == 1 and board[x+4][y] == 1:
                        if board[x][y] == 0:
                            h_value = 0 - 99999999
                            return h_value
                    # 플레이어가 세로 4 만드는 경우 + 아래쪽이 열려있는 경우
                    if x == 14:
                        for tmp_x in range(15, 19):
                            if board[tmp_x][y] == 1 and board[tmp_x][y + 1] == 1 and board[tmp_x][y + 2] == 1 and board[tmp_x][
                                y + 3] == 1:
                                if board[tmp_x][y + 4] == 0:
                                    h_value = 0 - 99999999
                                    return h_value
                    if board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 1 and board[x][y + 3] == 1:
                        if board[x][y + 4] == 0:
                            h_value = 0 - 99999999
                            return h_value
                    # 플레이어가 세로 4 만드는 경우 + 위쪽이 열려있는 경우
                    if x == 14:
                        for tmp_x in range(15, 19):
                            if board[tmp_x][y + 1] == 1 and board[tmp_x][y + 2] == 1 and board[tmp_x][y + 3] == 1 and board[tmp_x][
                                y + 4]:
                                if board[tmp_x][y + 4] == 0:
                                    h_value = 0 - 99999999
                                    return h_value
                    if board[x][y + 1] == 1 and board[x][y + 2] == 1 and board[x][y + 3] == 1 and board[x][y+4]:
                        if board[x][y + 4] == 0:
                            h_value = 0 - 99999999
                            return h_value
                    # 플레이어가 / 방향 대각선 4칸 만드는 경우 + 아래쪽이 열려있는 경우
                    if board[x + 4][y] == 1 and board[x + 3][y + 1] == 1 and board[x + 2][y + 2] == 1 and board[x + 1][
                        y + 3] == 1:
                        if board[x][y + 4] == 0:
                            h_value = 0 - 99999999
                            return h_value
                    # 플레이어가 / 방향 대각선 4칸 만드는 경우 + 위쪽이 열려있는 경우
                    if board[x + 3][y + 1] == 1 and board[x + 2][y + 2] == 1 and board[x + 1][y + 3] == 1 and board[x][y + 4] == 1:
                        if board[x + 4][y] == 0:
                            h_value = 0 - 99999999
                            return h_value
                    # 플레이어가 반대 방향 대각선 5칸 만드는 경우 + 아래쪽이 열려있는 경우
                    if board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 3] == 1:
                        if board[x + 4][y + 4] == 0:
                            h_value = 0 - 99999999
                            return h_value
                    # 플레이어가 반대 방향 대각선 5칸 만드는 경우 + 위쪽이 열려있는 경우
                    if board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][y + 3] == 1 and board[x+4][y+4] == 1:
                        if board[x][y] == 0:
                            h_value = 0 - 99999999
                            return h_value


        # depth 1일 때의 필수적인 요소는 위에서 처리 후, 아래로 진행



                # index error 방지를 위해 x == 0 따로 처리
                # 왼쪽 모서리가 막혀 있음
                if x == 0:
                    # AI 공격 고려
                    # AI가 가로 4를 만드는 경우
                    if board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 2 and board[x + 3][y] == 2:
                        if board[x + 4][y] == 0:
                            # if depth_endgame == 1:
                            # h_value = h_value + 99999999  # AI의 턴에 게임을 끝낼 수 있으면 확정
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 0 and board[x + 3][y] == 2:
                        if board[x + 4][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 0 and board[x + 2][y] == 2 and board[x + 3][y] == 2:
                        if board[x + 4][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 2:
                        h_value = h_value + 500

                    # AI가 세로 4를 만드는 경우
                    if board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 2 and board[x][y + 3] == 2:
                        if board[x][y + 4] == 0:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 0 and board[x][y + 2] == 2 and board[x][y + 3] == 2:
                        if board[x][y + 4] == 0:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 0 and board[x][y + 3] == 2:
                        if board[x][y + 4] == 0:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 2:
                        h_value = h_value + 100

                    # 반대 방향 대각선
                    if board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 3] == 2:
                        if board[x + 4][y + 4] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 0 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 3] == 2:
                        if board[x + 4][y + 4] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 3] == 2:
                        if board[x + 4][y + 4] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 2:
                        h_value = h_value + 500

                    # AI 수비 고려
                    if board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 1 and board[x + 3][y] == 1:
                        # 플레이어가 오른쪽이 열린 가로 4를 만들게 두면 감산
                        if board[x + 4][y] == 0:
                            # if depth_endgame == 2:
                            #    h_value = 0  # 마지막이 AI의 턴인데 플레이어가 4를 만들게 두는 수 제외
                            # else:
                            h_value = h_value - 500
                        # AI가 그 오른쪽을 막았으면 가산
                        elif board[x + 4][y] == 2:
                            # if depth_endgame == 1:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 0 and board[x + 3][y] == 1:
                        # 열린 3 (1101)
                        if board[x + 4][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y] == 0 and board[x + 2][y] == 1 and board[x + 3][y] == 1:
                        # 열린 3 (1011)
                        if board[x + 4][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2:
                            h_value = h_value + 500
                    # 열린 3 (111)
                    elif board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 1:
                        h_value = h_value - 500

                    # 플레이어가 아래로 열린 세로 4를 만들게 두면 감산
                    if board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 1 and board[x][y + 3] == 1:
                        if board[x][y + 4] == 0:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 0 and board[x][y + 3] == 1:
                        if board[x][y + 4] == 0:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 0 and board[x][y + 2] == 1 and board[x][y + 3] == 1:
                        if board[x][y + 4] == 0:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 1:
                        h_value = h_value - 500

                    # 반대 방향 대각선
                    if board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 3] == 1:
                        if board[x + 4][y + 4] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 0 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 3] == 1:
                        if board[x + 4][y + 4] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 3] == 1:
                        if board[x + 4][y + 4] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1:
                        h_value = h_value - 500


                # index error 방지를 위해 x==14 따로 처리
                elif x == 14:
                    # AI공격 고려
                    # AI가 가로 4 만드는 경우
                    if board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 2 and board[x + 3][y] == 2:
                        if board[x - 1][y] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 0 and board[x + 3][y] == 2:
                        if board[x - 1][y] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 0 and board[x + 2][y] == 2 and board[x + 3][y] == 2:
                        if board[x - 1][y] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 2:
                        h_value = h_value + 500

                    # AI가 세로 4 만드는 경우
                    if board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 2 and board[x][y + 3] == 2:
                        if board[x][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 0 and board[x][y + 3] == 2:
                        if board[x][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 0 and board[x][y + 2] == 2 and board[x][y + 3] == 2:
                        if board[x][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 2:
                        h_value = h_value + 500

                    # 대각선
                    if board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 3] == 2:
                        if board[x - 1][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 0 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 3] == 2:
                        if board[x - 1][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 3] == 2:
                        if board[x - 1][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 2:
                        h_value = h_value + 500


                    # AI 수비 고려
                    # 플레이어가 가로 4
                    if board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 1 and board[x + 3][y] == 1:
                        if board[x - 1][y] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y] == 0 and board[x + 2][y] == 1 and board[x + 3][y] == 1:
                        if board[x - 1][y] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 0 and board[x + 3][y] == 1:
                        if board[x - 1][y] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 1:
                        h_value = h_value - 500

                    # 플레이어가 세로 4
                    if board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 1 and board[x][y + 3] == 1:
                        if board[x][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 0 and board[x][y + 2] == 1 and board[x][y + 3] == 1:
                        if board[x][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 0 and board[x][y + 3] == 1:
                        if board[x][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 1:
                        h_value = h_value - 500

                    # 플레이어가 반대방향 대각선
                    if board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 3] == 1:
                        if board[x - 1][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 0 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 3] == 1:
                        if board[x - 1][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 3] == 1:
                        if board[x - 1][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1:
                        h_value = h_value - 500



                # x == 0, 14 예외처리 후
                else:
                    # 플레이어가 가로 4
                    if board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 1 and board[x + 3][y] == 1:
                        if board[x + 4][y] == 1 or board[x - 1][y] == 1:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 0 and board[x - 1][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 and board[x - 1][y] == 2:
                            h_value = h_value + 750
                        elif board[x + 4][y] == 2 or board[x - 1][y] == 2:
                            h_value = h_value + 250
                    elif board[x][y] == 1 and board[x + 1][y] == 0 and board[x + 2][y] == 1 and board[x + 3][y] == 1:
                        if board[x + 4][y] == 0 and board[x - 1][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 and board[x - 1][y] == 2:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 2 and board[x - 1][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 0 and board[x + 3][y] == 1:
                        if board[x + 4][y] == 0 and board[x - 1][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 and board[x - 1][y] == 2:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 2 or board[x - 1][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 1:
                        if board[x + 3][y] == 2 or board[x - 1][y] == 2:
                            h_value = h_value + 500
                        else:
                            h_value = h_value - 500

                    # 플레이어가 세로 4
                    if board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 1 and board[x][y + 3] == 1:
                        if board[x][y + 4] == 1 or board[x][y - 1] == 1:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 0 and board[x][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 2 and board[x][y - 1] == 2:
                            h_value = h_value + 750
                        elif board[x][y + 4] == 2 or board[x][y - 1] == 2:
                            h_value = h_value + 250
                    elif board[x][y] == 1 and board[x][y + 1] == 0 and board[x][y + 2] == 1 and board[x][y + 3] == 1:
                        if board[x][y + 4] == 0 and board[x][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 2 and board[x][y - 1] == 2:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 2 or board[x][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 0 and board[x][y + 3] == 1:
                        if board[x][y + 4] == 0 and board[x][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 2 and board[x][y - 1] == 2:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 2 or board[x][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x][y + 1] == 1 and board[x][y + 2] == 1:
                        if board[x][y + 3] == 2 or board[x][y - 1] == 2:
                            h_value = h_value + 500
                        else:
                            h_value = h_value - 500

                    # 플레이어가 반대방향 대각선
                    if board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 3] == 1:
                        if board[x + 4][y + 4] == 1 or board[x - 1][y - 1] == 1:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 0 and board[x - 1][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 2 and board[x - 1][y - 1] == 2:
                            h_value = h_value + 750
                        elif board[x + 4][y + 4] == 2 or board[x - 1][y - 1] == 2:
                            h_value = h_value + 250
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 0 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 3] == 1:
                        if board[x + 4][y + 4] == 0 and board[x - 1][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 2 and board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 2 or board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 3] == 1:
                        if board[x + 4][y + 4] == 0 and board[x - 1][y - 1] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 2 and board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 2 or board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y] == 1 and board[x + 1][y + 1] == 1 and board[x + 2][y + 2] == 1:
                        if board[x + 3][y + 3] == 2 or board[x - 1][y - 1] == 2:
                            h_value = h_value + 500
                        else:
                            h_value = h_value - 500

                    # AI 공격 고려
                    # AI 가로 4
                    if board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 2 and board[x + 3][y] == 2:
                        if board[x + 4][y] == 0 or board[x - 1][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1 or board[x - 1][y] == 1:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 or board[x - 1][y] == 2:
                            h_value = h_value + 750
                    elif board[x][y] == 2 and board[x + 1][y] == 0 and board[x + 2][y] == 2 and board[x + 3][y] == 2:
                        if board[x + 4][y] == 0 or board[x - 1][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1 or board[x - 1][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 0 and board[x + 3][y] == 2:
                        if board[x + 4][y] == 0 or board[x - 1][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1 or board[x - 1][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 2:
                        h_value = h_value + 500

                    # AI 세로 4
                    if board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 2 and board[x][y + 3] == 2:
                        if board[x][y + 4] == 0 or board[x][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 1 or board[x][y - 1] == 1:
                            h_value = h_value - 500
                        elif board[x][y + 4] == 2 or board[x][y - 1] == 2:
                            h_value = h_value + 750
                    elif board[x][y] == 2 and board[x][y + 1] == 0 and board[x][y + 2] == 2 and board[x][y + 3] == 2:
                        if board[x][y + 4] == 0 or board[x][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 1 or board[x][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 0 and board[x][y + 3] == 2:
                        if board[x][y + 4] == 0 or board[x][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x][y + 4] == 1 or board[x][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x][y + 1] == 2 and board[x][y + 2] == 2:
                        h_value = h_value + 500

                    # AI가 반대방향 대각선
                    if board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 3] == 2:
                        if board[x + 4][y + 4] == 0 or board[x - 1][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 1 or board[x - 1][y - 1] == 1:
                            h_value = h_value - 500
                        elif board[x + 4][y + 4] == 2 or board[x - 1][y - 1] == 2:
                            h_value = h_value + 750
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 0 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 3] == 2:
                        if board[x + 4][y + 4] == 0 or board[x - 1][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 1 or board[x - 1][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 3] == 2:
                        if board[x + 4][y + 4] == 0 or board[x - 1][y - 1] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y + 4] == 1 or board[x - 1][y - 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y] == 2 and board[x + 1][y + 1] == 2 and board[x + 2][y + 2] == 2:
                        h_value = h_value + 500

        # 나머지 대각선 확인
        for x in range(0, 15):
            for y in range(0, 15):
                if x == 0:
                    if board[x][y+4] == 1 and board[x + 1][y + 3] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 1] == 1:
                        if board[x + 4][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y +3] == 0 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y +1] == 1:
                        if board[x + 4][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y +3] == 1 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y +1] == 1:
                        if board[x + 4][y] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y +3] == 1 and board[x + 2][y + 2] == 1:
                        h_value = h_value - 500

                    if board[x][y+4] == 2 and board[x + 1][y + 3] == 2 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y +1] == 2:
                        if board[x + 4][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y+3] == 0 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y +1] == 2:
                        if board[x + 4][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y + 3] == 2 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y +1] == 2:
                        if board[x + 4][y] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y+3] == 2 and board[x + 2][y+2] == 2:
                        h_value = h_value + 500

                elif x == 14:
                    if board[x][y+4] == 1 and board[x + 1][y + 3] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 1] == 1:
                        if board[x - 1][y + 1] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y + 3] == 0 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 1] == 1:
                        if board[x - 1][y + 1] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y + 3] == 1 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 1] == 1:
                        if board[x - 1][y + 1] == 0:
                            h_value = h_value - 500
                        elif board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y + 3] == 1 and board[x + 2][y + 2] == 1:
                        h_value = h_value - 500


                    if board[x][y+4] == 2 and board[x + 1][y + 3] == 2 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 1] == 2:
                        if board[x - 1][y + 1] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y + 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y + 3] == 0 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 1] == 2:
                        if board[x - 1][y + 1] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y + 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y + 3] == 2 and board[x + 2][y + 2] == 0 and board[x + 3][
                        y + 1] == 2:
                        if board[x - 1][y + 1] == 0:
                            h_value = h_value + 500
                        elif board[x - 1][y + 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y + 3] == 2 and board[x + 2][y + 2] == 2:
                        h_value = h_value + 500

                else:
                    if board[x][y+4] == 1 and board[x + 1][y + 3] == 1 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 1] == 1:
                        if board[x + 4][y] == 1 or board[x - 1][y + 1] == 1:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 0 and board[x - 1][y + 1] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 and board[x - 1][y + 1] == 2:
                            h_value = h_value + 750
                        elif board[x + 4][y] == 2 or board[x - 1][y + 1] == 2:
                            h_value = h_value + 250
                    elif board[x][y+4] == 1 and board[x + 1][y + 3] == 0 and board[x + 2][y + 2] == 1 and board[x + 3][
                        y + 1] == 1:
                        if board[x + 4][y] == 0 and board[x - 1][y + 1] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 and board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 2 or board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y] == 1 and board[x + 2][y] == 0 and board[x + 3][y] == 1:
                        if board[x + 4][y] == 0 and board[x - 1][y + 1] == 0:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 and board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 2 or board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                    elif board[x][y+4] == 1 and board[x + 1][y + 3] == 1 and board[x + 2][y + 2] == 1:
                        if board[x + 3][y + 1] == 2 and board[x - 1][y + 1] == 2:
                            h_value = h_value + 500
                        else:
                            h_value = h_value - 500


                    if board[x][y+4] == 2 and board[x + 1][y + 3] == 2 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 1] == 2:
                        if board[x + 4][y] == 0 or board[x - 1][y + 1] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1 or board[x - 1][y + 1] == 1:
                            h_value = h_value - 500
                        elif board[x + 4][y] == 2 or board[x - 1][y + 1] == 2:
                            h_value = h_value + 750
                    elif board[x][y+4] == 2 and board[x + 1][y + 3] == 0 and board[x + 2][y + 2] == 2 and board[x + 3][
                        y + 1] == 2:
                        if board[x + 4][y] == 0 or board[x - 1][y + 1] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1 or board[x - 1][y + 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y] == 2 and board[x + 2][y] == 0 and board[x + 3][y] == 2:
                        if board[x + 4][y] == 0 or board[x - 1][y + 1] == 0:
                            h_value = h_value + 500
                        elif board[x + 4][y] == 1 or board[x - 1][y + 1] == 1:
                            h_value = h_value - 500
                    elif board[x][y+4] == 2 and board[x + 1][y + 3] == 2 and board[x + 2][y + 2] == 2:
                        h_value = h_value + 500



        # 시간초과시 0.1 return
        if (time.time() - time_std) > time_preset:
            return 0.1
        else:
            return h_value

# 메뉴 클래스
class Menu(object):
    def __init__(self, surface):
        self.font = pygame.font.Font('freesansbold.ttf', 22)
        self.surface = surface
        self.draw_menu()

    def draw_menu(self):
        self.new_rect = self.make_text(self.font, 'New Game', white, None, window_height - 330, window_width - 160)
        self.quit_rect = self.make_text(self.font, 'Quit Game', white, None, window_height - 300, window_width - 160)

    def show_msg(self, msg_id):
        msg = {
            empty: '          ',
            player: 'The winner is Player',
            ai: 'The winner is AI',
            tie: 'Draw',
        }
        center_x = window_width - (window_width - board_width) // 2
        self.make_text(self.font, msg[msg_id], black, bg_colour, 30, center_x, 1)

    def make_text(self, font, text, color, bgcolor, top, left, position=0):
        surf = font.render(text, False, color, bgcolor)
        rect = surf.get_rect()
        if position:
            rect.center = (left, top)
        else:
            rect.topleft = (left, top)
        self.surface.blit(surf, rect)
        return rect


    def check_rect(self, pos, omok):
        global player_num
        global time_std
        # 새 게임
        if self.new_rect.collidepoint(pos):
            omok.start = 0
            return True
        # 게임 종료
        elif self.quit_rect.collidepoint(pos):
            self.terminate()
        # 선공 후공 선택
        # 선공
        elif omok.menu.black_rect.collidepoint(pos):
            if not omok.start:
                player_num = 1  # 선후공 관계없이 player_num은 1
                omok.turn = 1  # 오목알을 draw하기 편하게 따로 흑 백에따른 숫자 구분
                time_std = time.time()
                omok.menu.bw = self.make_text(self.font, '', white, None, 50, window_width - 160)
                omok.menu.black_rect = self.make_text(self.font, '', white, None, 80, window_width - 160)
                omok.menu.white_rect = self.make_text(self.font, '', white, None, 110, window_width - 160)
                omok.start = 1
        # 후공
        elif omok.menu.white_rect.collidepoint(pos):
            if not omok.start:
                player_num = 1  # 선후공 관계없이 player_num은 1
                omok.turn = 2  # 오목알을 draw하기 편하게 따로 흑 백에따른 숫자 구분
                # ai가 첫 수 진행 ( 중앙 근처에 적당히 하나 두도록 함)
                ai_xy = (random.randint(7, 10), random.randint(7, 10))
                ai_coord = ((ai_xy[0] * grid_size + 25), (ai_xy[1] * grid_size + 25))
                omok.draw_stone(ai_coord, omok.turn, 3 - omok.turn)
                self.make_text(self.font, '  ', white, None, 50, window_width - 160)
                self.make_text(self.font, '  ', white, None, 80, window_width - 160)
                self.make_text(self.font, '  ', white, None, 110, window_width - 160)
                omok.start = 1
                time_std = time.time()
        return False

    def terminate(self):
        pygame.quit()
        sys.exit()

    def is_continue(self, omok):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.terminate()
                elif event.type == MOUSEBUTTONUP:
                    if (self.check_rect(event.pos, omok)):
                        return
            pygame.display.update()
            fps_clock.tick(fps)


if __name__ == '__main__':
    main()





