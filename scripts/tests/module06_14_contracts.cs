using OrderTool.Domain;
using OrderTool.Domain.Pricing;
using OrderTool.Application;
using OrderTool.Infrastructure;
using OrderTool.Presentation;
using OrderTool.Testing;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var day=new DateOnly(2026,7,31);var harness=new CharacterizationHarness(Run);var cases=new List<string[]>{Array.Empty<string>(),new[]{"a|gold|Ha Noi|x:1:0"},new[]{"a|standard|Hue|x:1:500000"},new[]{"a|gold|ha noi|x:5:10"},new[]{"a|gold|Hue|x:abc:1","b|gold|Hue|x:1:-1","c|standard","d|gold|Hue|"}};
 var random=new Random(12345);for(int i=0;i<100;i++)cases.Add(new[]{$"id-{i}|{(i%2==0?"gold":"standard")}|{(i%3==0?"Ha Noi":"Hue")}|x:{random.Next(1,10)}:{random.Next(0,1000000)}"});
 foreach(var input in cases)Check(harness.Compare("boundary",input,day).Matches,"legacy-compatible input");
 var parser=new OrderParser();foreach(string invalid in new[]{"|gold|Hue|x:1:1","a|gold||x:1:1","a|gold|Hue| :1:1"})Check(!parser.Parse(invalid).IsValid,"blank fields rejected as results");
 var order=parser.Parse("a|gold|Hue|x:1:100").Order!;Throws<NotSupportedException>(()=>((ICollection<OrderLine>)order.Lines).Clear());Check(order.Lines.Count==1,"domain invariant view");
 var capped=new DiscountEngine(new IDiscountRule[]{new FixedRule()},.1m);Check(capped.ComputeDiscount(order).Amount==10,"actual cap branch");
 var temp=Path.Combine(Path.GetTempPath(),Guid.NewGuid().ToString("N"));Directory.CreateDirectory(temp);
 try {var path=Path.Combine(temp,"report.txt");var writer=new FileReportWriter(path);writer.Write("old");writer.Write("new");Check(File.ReadAllText(path)=="new" && !File.Exists(path+".tmp"),"file roundtrip");
  Directory.CreateDirectory(path+".tmp");Throws<UnauthorizedAccessException>(()=>writer.Write("broken"));Check(File.ReadAllText(path)=="new","failed temp write preserves old report");
  var sourcePath=Path.Combine(temp,"input.txt");File.WriteAllText(sourcePath,"a|gold|Hue|x:1:1\n\n");Check(new TextFileOrderSource(sourcePath).ReadAll().Count==1,"file source skips blank lines");
 }finally{Directory.Delete(temp,true);}
 var output=new InMemoryReportWriter();output.Write("old");var broken=Build(new InMemoryOrderSource(new[]{"a|gold|Hue|x:2:79228162514264337593543950335"}),output,day);Throws<OverflowException>(()=>broken.Execute());Check(output.LastReport=="old","no writer before pricing completes");

 }

 sealed class FixedRule:IDiscountRule {public string Code=>"fixed";public Money ComputeDiscount(Order o)=>Money.Of(1000);}
 static ProcessResult Run(IReadOnlyList<string> input,DateOnly day)=>Build(new InMemoryOrderSource(input),new InMemoryReportWriter(),day).Execute();
 static ProcessOrdersUseCase Build(IOrderSource source,IReportWriter writer,DateOnly day)=>new(new OrderParser(),new PricingService(new DiscountEngine(new IDiscountRule[]{new TierDiscountRule(CustomerTier.Gold,.05m),new VolumeDiscountRule(5,.03m)},.1m),new ShippingPolicy(Money.Of(500000),"Ha Noi",Money.Of(20000),Money.Of(35000)),new TaxPolicy(.08m)),new ReportBuilder(),source,writer,new FixedClock(day));

}
