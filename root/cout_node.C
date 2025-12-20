//
// k4geo/utils/dd4hep2root.py -c ${COMPACT} -o KITP_10TeV_ITOT_doublets_v01.root
//

int cout_node() {
  const auto fi = new TFile("KITP_10TeV_ITOT_doublets_v01.root");
  std::cout << "Got file " << fi << std::endl;

  const auto geo = (TGeoManager*)(fi->Get("default"));
  std::cout << "Got geo " << geo << std::endl;

  std::vector<float> xs{};
  std::vector<float> ys{};
  std::vector<float> zs{};

  // nb: these units are cm
  xs.push_back(-16.332); ys.push_back(-29.999); zs.push_back(-17.951);
  xs.push_back(-7.789); ys.push_back(-33.263); zs.push_back(11.577);
  xs.push_back(-8.063); ys.push_back(33.202); zs.push_back(9.541);
  xs.push_back(-15.615); ys.push_back(-30.582); zs.push_back(17.818);
  xs.push_back(-32.304); ys.push_back(10.358); zs.push_back(-4.292);
  xs.push_back(20.161); ys.push_back(-27.551); zs.push_back(-4.652);
  xs.push_back(8.324); ys.push_back(33.069); zs.push_back(-7.438);
  xs.push_back(-29.221); ys.push_back(-17.293); zs.push_back(6.243);
  xs.push_back(31.248); ys.push_back(13.790); zs.push_back(-15.544);
  xs.push_back(15.347); ys.push_back(30.234); zs.push_back(12.940);
  xs.push_back(-20.087); ys.push_back(-27.295); zs.push_back(-12.462);
  xs.push_back(-1.175); ys.push_back(-34.283); zs.push_back(-19.068);
  xs.push_back(20.233); ys.push_back(27.224); zs.push_back(3.829);

  for (size_t i=0; i < xs.size(); ++i) {
    const auto x = xs[i];
    const auto y = ys[i];
    const auto z = zs[i];
    const auto node = geo->FindNode(x, y, z);
    std::cout << "x, y, z: " << x << " " << y << " " << z << std::endl;
    std::cout << "Volume: " << node->GetVolume()->GetName() << std::endl;
    std::cout << "Material: " << node->GetVolume()->GetMaterial()->GetName() << std::endl;
  }

  return 0;
}

