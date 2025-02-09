import torch
import torch.nn as nn
from Hyperparameters import Hyperparameters as hp



def Ecos_sim(V_F_single, A_F_single, margin=0):  # vision feature, audio feature
    # vision = tensor[batch_size, channels, Height, Wide] -> tensor[channels, Height, Wide]
    # audio  = tensor[batch_szie, channels, Wide]         -> tensor[channels, Wide]

    #sizeV = V_F.size()
    #sizeA = A_F.size()

    #V_F = V_F.view(sizeV[0] * sizeV[1], sizeV[2])
    #A_F = A_F.view(sizeA[0] * sizeA[0])

    upper = V_F_single.mm(A_F_single.t())

    V_F_norm = torch.sqrt((V_F_single ** 2).sum() + 1e-18)
    A_F_norm = torch.sqrt((A_F_single ** 2).sum(0) + 1e-18)

    sim = upper / (V_F_norm * A_F_norm)

    e_sim = torch.exp(sim - margin)

    return e_sim              # 只是算一个样本的


class ContrastiveLoss(nn.Module):
    def __init__(self,num=32):  # 假设默认num=32是batch_size
        super(ContrastiveLoss, self).__init__()
        self.num = num
        self.cos_sim = nn.CosineSimilarity(dim=1, eps=1e-18)


    def forward(self, pre_VF, pre_AF, back_VF, back_AF):
        sim_pre = []
        #sim_back_V = []
        #sim_back_V_down = []
        #sim_back_A = []
        #sim_back_A_down = []
        # size = batch_size
        size = pre_VF.size(0)


        #for i in range(0, size):
        #    sim_pre += torch.log(Ecos_sim(pre_VF[:i, ], pre_AF[:i, ])) # [batch_size, 2048]

        sim_pre = self.cos_sim(pre_VF, pre_AF)   # 先行算一个普通的cos_sim
#######################################################################
        if self.num == hp.batch_size:
            for i in range(0, size):  # vision to audio, 一个i算一个样本的loss
                # now = back_VF[i]
                if self.num == hp.batch_size:
                    for j in range(0, size):
                        #for j in range(0, size):
                        if j == i:
                            continue
                        negtive = Ecos_sim(back_VF[i], back_AF[j])
                        if j == 0:
                            sim_back_V_down = negtive
                        else:
                            sim_back_V_down += negtive

                positive = Ecos_sim(back_VF[i], back_AF[i], margin=hp.margin)

                if i == 0:
                    sim_back_V = torch.log(positive/ positive + sim_back_V_down)
                else:
                    sim_back_V = torch.cat((sim_back_V, torch.log(positive / positive + sim_back_V_down)), 0)

        else:
            for i in range(0, size):  # 从这个之后取，到末尾了还没取到对应数量，从头接着取
                for j in range(i, i + size):
                    negtive = Ecos_sim(back_VF[i], back_AF[j])
                    if i == 0:
                        sim_back_V_down = negtive

                    if j == size:
                        breakpoint = j
                        for j in range(1, size - breakpoint):
                            sim_back_V_down += negtive

                positive = Ecos_sim(back_VF[i], back_AF[i], margin=self.margin)

                if i == 0:
                    sim_back_V = torch.log(positive / positive + sim_back_V_down)
                else:
                    sim_back_V = torch.cat((sim_back_V, torch.log(positive / positive + sim_back_V_down)), 0)
#######################################################################
        if self.num == hp.batch_size:
            for i in range(0, size):  # audio to vision
                # now = back_AF[i]
                if self.num == hp.batch_size:
                    for j in range(0, size):
                        if j == i:
                            continue
                        negtive = Ecos_sim(back_AF[i], back_VF[j])
                        if j == 0:
                            sim_back_A_down = negtive
                        else:
                            sim_back_A_down += negtive

                positive = Ecos_sim(back_AF[i], back_VF[i], margin=hp.margin)

                if i == 0:
                    sim_back_A = torch.log(positive / positive + sim_back_A_down)
                else:
                    sim_back_A = torch.cat((sim_back_A, torch.log(positive / positive + sim_back_A_down)), 0)
        else:
            for i in range(0, size):  # 从这个之后取，到末尾了还没取到对应数量，从头接着取
                for j in range(i, i + size):
                    negtive = Ecos_sim(back_AF[i], back_VF[j])
                    if j == 0:
                        sim_back_A_down = negtive
                    if j == size:
                        breakpoint = j
                        for j in range(1, size - breakpoint):
                                sim_back_A_down += negtive

                positive = Ecos_sim(back_VF[i], back_AF[i], margin=hp.margin)

                if i == 0:
                    sim_back_A = torch.log(positive/ positive + sim_back_A_down)
                else:
                    sim_back_A = torch.cat((sim_back_A, torch.log(positive / positive + sim_back_V_down)), 0)



        return hp.balance_parameter * (- 1 / hp.bias * (sim_back_V + sim_back_A)) + (1 - hp.balance_parameter) * sim_pre